"""Trial-Extraction Agent — pulls structured data from each trial-like study.

Live: one batched Claude (Haiku) call extracts fields per study, closed-book over
the provided abstracts, with a hard rule to emit null when a value is not reported
(never infer effect sizes). Offline: deterministic regex/keyword parsing of the
abstract. Only trial-like designs (RCT, registered trial, meta-analysis, systematic
review) are extracted; guidelines and labels are handled by their own agents.
"""

from __future__ import annotations

import logging
import re

from app.agents.base import Agent, AgentOutcome, PipelineState
from app.agents.specialists import mentions
from app.core.config import get_settings
from app.llm.client import llm_live_enabled, structured_call
from app.rag.ranking import RankedDoc

log = logging.getLogger("agents.extraction")

_TRIAL_DESIGNS = {"rct", "trial_registry", "meta_analysis", "systematic_review"}
_MAX_EXTRACT = 8

# Common adverse-event terms we can detect deterministically offline.
_AE_TERMS = (
    "hypotension", "dizziness", "hyperkalemia", "headache", "nausea", "cough",
    "hypoglycemia", "hypoglycaemia", "diarrhea", "diarrhoea", "fatigue", "rash",
    "angioedema", "acute kidney injury", "bradycardia", "edema", "oedema",
)

_num = r"([0-9]+(?:\.[0-9]+)?)"


def _first(pattern: str, text: str) -> str | None:
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1) if m else None


def _offline_extract(rd: RankedDoc, a: str, b: str, topic: str) -> dict:
    abstract = rd.doc.abstract or ""
    low = abstract.lower()

    hr = _first(rf"\bHR\s*=?\s*{_num}", abstract)
    rr = _first(rf"\bRR\s*=?\s*{_num}", abstract)
    ci = _first(rf"95%\s*CI\s*({_num}\s*(?:-|–|to)\s*{_num})", abstract)
    ci = ci if ci else _first(r"95%\s*CI\s*([0-9.]+\s*(?:-|–|to)\s*[0-9.]+)", abstract)
    p = _first(rf"\bp\s*[=<]\s*{_num}", abstract)

    which = [m for m in (a, b) if mentions(rd, m)]
    intervention = " / ".join(which) if which else None
    comparator = None
    if "placebo" in low:
        comparator = "Placebo"
    elif "standard of care" in low or "active-controlled" in low or "active controlled" in low:
        comparator = "Standard of care / active comparator"

    population = None
    if "adults" in low or "adult" in low:
        population = "Adults with the target condition"

    outcomes: list[str] = []
    if "composite endpoint" in low or "composite" in low:
        outcomes.append("Composite clinical endpoint")
    if "primary outcome" in low or "primary endpoint" in low:
        outcomes.append("Primary outcome as pre-specified")

    adverse = sorted({term.title() for term in _AE_TERMS if term in low})

    strengths: list[str] = []
    if rd.doc.study_design in ("rct", "trial_registry"):
        strengths.append("Randomized design")
    if "double-blind" in low or "double blind" in low:
        strengths.append("Double-blind")
    if rd.doc.study_design in ("meta_analysis", "systematic_review"):
        strengths.append("Pools multiple studies")
    if (rd.doc.sample_size or 0) >= 1000:
        strengths.append("Large sample size")

    limitations: list[str] = []
    if not (mentions(rd, a) and mentions(rd, b)):
        limitations.append("Does not directly compare both molecules")
    if p and float(p) > 0.05:
        limitations.append("Primary result not statistically significant")
    if rd.doc.metadata.get("synthetic"):
        limitations.append("Synthetic offline placeholder — not a real study")

    return {
        "ref_key": rd.ref_key,
        "title": rd.doc.title,
        "study_design": rd.doc.study_design,
        "population": population,
        "intervention": intervention,
        "comparator": comparator,
        "sample_size": rd.doc.sample_size,
        "outcomes": outcomes,
        "hazard_ratio": f"HR {hr}" if hr else None,
        "relative_risk": f"RR {rr}" if rr else None,
        "confidence_interval": f"95% CI {ci}" if ci else None,
        "p_value": f"p={p}" if p else None,
        "adverse_events": adverse,
        "strengths": strengths,
        "limitations": limitations,
        "extractor_model": "offline-parse",
    }


_ITEM_PROPS = {
    "ref_key": {"type": "string"},
    "population": {"type": ["string", "null"]},
    "intervention": {"type": ["string", "null"]},
    "comparator": {"type": ["string", "null"]},
    "outcomes": {"type": "array", "items": {"type": "string"}},
    "hazard_ratio": {"type": ["string", "null"]},
    "relative_risk": {"type": ["string", "null"]},
    "confidence_interval": {"type": ["string", "null"]},
    "p_value": {"type": ["string", "null"]},
    "adverse_events": {"type": "array", "items": {"type": "string"}},
    "strengths": {"type": "array", "items": {"type": "string"}},
    "limitations": {"type": "array", "items": {"type": "string"}},
}

_EXTRACT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "extractions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": _ITEM_PROPS,
                "required": list(_ITEM_PROPS.keys()),
            },
        }
    },
    "required": ["extractions"],
}

_SYSTEM = (
    "You are a clinical-trial data-extraction engine. For each study you are given, "
    "extract structured fields using ONLY the provided title and abstract. Critical "
    "rules: if a value (hazard ratio, relative risk, confidence interval, p-value, "
    "population, comparator) is not explicitly reported in the text, return null for "
    "it — never infer, estimate, or fabricate a number. Echo back each study's ref_key "
    "exactly. Keep list items short."
)


class TrialExtractionAgent(Agent):
    key = "extraction"
    label = "Trial-Extraction Agent"
    model = "claude-haiku-4-5"

    async def run(self, state: PipelineState) -> AgentOutcome:
        a, b, t = state.molecule_a, state.molecule_b, state.topic
        targets = [rd for rd in state.verified if rd.doc.study_design in _TRIAL_DESIGNS][
            :_MAX_EXTRACT
        ]
        if not targets:
            state.extractions = []
            return AgentOutcome(detail="no trial-like studies to extract")

        by_key = {rd.ref_key: rd for rd in targets}
        # Deterministic offline extraction is always computed as the baseline/fallback.
        offline = {rd.ref_key: _offline_extract(rd, a, b, t) for rd in targets}
        extractions = dict(offline)
        model_used: str | None = None
        in_tok = out_tok = 0
        cost = 0.0

        if llm_live_enabled():
            try:
                lines = [
                    f"[{rd.ref_key}] {rd.doc.title}\n    abstract: {rd.doc.abstract[:900]}"
                    for rd in targets
                ]
                res = await structured_call(
                    model=get_settings().model_extract,
                    system=_SYSTEM,
                    user=(
                        f"Molecule A: {a}\nMolecule B: {b}\nTopic: {t}\n\n"
                        "Studies:\n" + "\n\n".join(lines)
                    ),
                    schema=_EXTRACT_SCHEMA,
                    max_tokens=4000,
                )
                model_used, in_tok, out_tok, cost = (
                    res.model, res.input_tokens, res.output_tokens, res.cost_usd
                )
                for item in res.data.get("extractions", []):
                    rk = item.get("ref_key")
                    rd = by_key.get(rk)
                    if rd is None:
                        continue  # drop invented ref_keys (anti-hallucination)
                    extractions[rk] = {
                        "ref_key": rk,
                        "title": rd.doc.title,
                        "study_design": rd.doc.study_design,
                        "population": item.get("population"),
                        "intervention": item.get("intervention"),
                        "comparator": item.get("comparator"),
                        "sample_size": rd.doc.sample_size,
                        "outcomes": item.get("outcomes", []),
                        "hazard_ratio": item.get("hazard_ratio"),
                        "relative_risk": item.get("relative_risk"),
                        "confidence_interval": item.get("confidence_interval"),
                        "p_value": item.get("p_value"),
                        "adverse_events": item.get("adverse_events", []),
                        "strengths": item.get("strengths", []),
                        "limitations": item.get("limitations", []),
                        "extractor_model": res.model,
                    }
            except Exception as exc:  # noqa: BLE001
                log.warning("live extraction failed, using offline parse: %s", exc)

        # Preserve ranking order.
        state.extractions = [extractions[rd.ref_key] for rd in targets]
        state.snapshot["extractions"] = len(state.extractions)
        return AgentOutcome(
            detail=f"extracted {len(state.extractions)} study record(s)",
            model=model_used,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost_usd=cost,
        )

"""Clinical Question Interpreter — the first agent in the V3 pipeline.

Turns the raw user request (Drug A, Drug B, clinical topic) into a structured
research plan: a PICO framework, drug-name synonyms/alternatives, relevant disease
terms, and an expanded keyword set. Downstream the Search Agent uses the expanded
terms to build broader, higher-recall queries.

Live: Claude (Sonnet) proposes the plan with a structured output. Offline: a
deterministic plan derived from the inputs plus a small built-in synonym lexicon,
so the pipeline is fully testable with no network or API keys.
"""

from __future__ import annotations

import logging

from app.agents.base import Agent, AgentOutcome, PipelineState
from app.core.config import get_settings
from app.llm.client import llm_live_enabled, structured_call

log = logging.getLogger("agents.interpreter")

# Small offline lexicon: brand/alternative names for common comparison molecules.
# Only used to widen offline recall; never a source of clinical claims.
_SYNONYMS: dict[str, list[str]] = {
    "telmisartan": ["Micardis", "angiotensin receptor blocker", "ARB"],
    "valsartan": ["Diovan", "angiotensin receptor blocker", "ARB"],
    "empagliflozin": ["Jardiance", "SGLT2 inhibitor"],
    "dapagliflozin": ["Farxiga", "Forxiga", "SGLT2 inhibitor"],
    "atorvastatin": ["Lipitor", "statin", "HMG-CoA reductase inhibitor"],
    "rosuvastatin": ["Crestor", "statin", "HMG-CoA reductase inhibitor"],
    "apixaban": ["Eliquis", "DOAC", "factor Xa inhibitor"],
    "rivaroxaban": ["Xarelto", "DOAC", "factor Xa inhibitor"],
    "metformin": ["Glucophage", "biguanide"],
    "semaglutide": ["Ozempic", "Wegovy", "GLP-1 receptor agonist"],
    "liraglutide": ["Victoza", "Saxenda", "GLP-1 receptor agonist"],
    "lisinopril": ["Prinivil", "Zestril", "ACE inhibitor"],
    "losartan": ["Cozaar", "angiotensin receptor blocker", "ARB"],
}


def _syn(name: str) -> list[str]:
    return _SYNONYMS.get(name.strip().lower(), [])


def _offline_plan(a: str, b: str, topic: str) -> dict:
    """Deterministic research plan when no LLM is available."""
    return {
        "pico": {
            "population": f"Adults for whom {a} or {b} is being considered for {topic}",
            "intervention": a,
            "comparator": b,
            "outcome": topic,
        },
        "synonyms": {a: _syn(a), b: _syn(b)},
        "disease_terms": [topic],
        "expanded_keywords": sorted(
            {a, b, topic, *_syn(a), *_syn(b)}, key=str.lower
        ),
        "planner_model": "offline-plan",
    }


_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "population": {"type": "string"},
        "intervention": {"type": "string"},
        "comparator": {"type": "string"},
        "outcome": {"type": "string"},
        "synonyms_a": {"type": "array", "items": {"type": "string"}},
        "synonyms_b": {"type": "array", "items": {"type": "string"}},
        "disease_terms": {"type": "array", "items": {"type": "string"}},
        "expanded_keywords": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "population",
        "intervention",
        "comparator",
        "outcome",
        "synonyms_a",
        "synonyms_b",
        "disease_terms",
        "expanded_keywords",
    ],
}

_SYSTEM = (
    "You are a clinical research librarian building a search plan to compare two "
    "drugs for a clinical topic. Produce a PICO framework, known brand/alternative "
    "names for each drug, relevant disease/MeSH-style terms, and an expanded keyword "
    "set for a high-recall literature search. Use only well-established drug and "
    "disease terminology; do not invent trial names, effect sizes, or citations."
)


class ClinicalQuestionInterpreterAgent(Agent):
    key = "interpreter"
    label = "Clinical-Question Interpreter"
    model = "claude-sonnet-5"

    async def run(self, state: PipelineState) -> AgentOutcome:
        a, b, t = state.molecule_a, state.molecule_b, state.topic
        plan = _offline_plan(a, b, t)
        model_used: str | None = None
        in_tok = out_tok = 0
        cost = 0.0

        if llm_live_enabled():
            try:
                res = await structured_call(
                    model=get_settings().model_agent,
                    system=_SYSTEM,
                    user=f"Drug A: {a}\nDrug B: {b}\nClinical topic: {t}",
                    schema=_SCHEMA,
                    max_tokens=1200,
                )
                d = res.data
                # Merge live terms with the offline lexicon (union widens recall).
                syn_a = sorted({*_syn(a), *d.get("synonyms_a", [])}, key=str.lower)
                syn_b = sorted({*_syn(b), *d.get("synonyms_b", [])}, key=str.lower)
                keywords = sorted(
                    {a, b, t, *syn_a, *syn_b, *d.get("expanded_keywords", [])},
                    key=str.lower,
                )
                plan = {
                    "pico": {
                        "population": d.get("population") or plan["pico"]["population"],
                        "intervention": d.get("intervention") or a,
                        "comparator": d.get("comparator") or b,
                        "outcome": d.get("outcome") or t,
                    },
                    "synonyms": {a: syn_a, b: syn_b},
                    "disease_terms": d.get("disease_terms") or [t],
                    "expanded_keywords": keywords,
                    "planner_model": res.model,
                }
                model_used, in_tok, out_tok, cost = (
                    res.model, res.input_tokens, res.output_tokens, res.cost_usd
                )
            except Exception as exc:  # noqa: BLE001
                log.warning("live interpreter failed, using offline plan: %s", exc)

        state.research_plan = plan
        state.snapshot["research_plan"] = plan
        n_terms = len(plan["expanded_keywords"])
        n_disease = len(plan["disease_terms"])
        return AgentOutcome(
            detail=f"PICO built; {n_terms} search terms across {n_disease} disease term(s)",
            model=model_used,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost_usd=cost,
        )

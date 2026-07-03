from __future__ import annotations

import logging

from app.agents.specialists import analyze, head_to_head
from app.core.config import get_settings
from app.llm.models import cost_usd
from app.pipeline.comparison import build_comparison, top_tier_label
from app.rag.grade import grade
from app.rag.ranking import RankedDoc, confidence_from

log = logging.getLogger("llm.synthesizer")

# JSON schema for structured report synthesis (used in live Claude mode).
REPORT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "section_key": {"type": "string"},
                    "title": {"type": "string"},
                    "confidence": {
                        "type": "string",
                        "enum": ["high", "moderate", "low", "very_low"],
                    },
                    "insufficient_evidence": {"type": "boolean"},
                    "claims": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "text": {"type": "string"},
                                "citation_ids": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                            "required": ["text", "citation_ids"],
                        },
                    },
                },
                "required": [
                    "section_key", "title", "confidence", "insufficient_evidence", "claims",
                ],
            },
        },
        "comparison": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "attribute": {"type": "string"},
                    "value_a": {"type": "string"},
                    "value_b": {"type": "string"},
                    "confidence": {
                        "type": "string",
                        "enum": ["high", "moderate", "low", "very_low"],
                    },
                    "citation_ids": {"type": "array", "items": {"type": "string"}},
                    "rationale": {"type": "string"},
                },
                "required": [
                    "attribute", "value_a", "value_b", "confidence", "citation_ids", "rationale",
                ],
            },
        },
    },
    "required": ["sections", "comparison"],
}

SYSTEM_PROMPT = (
    "You are a clinical evidence synthesis engine. You compare two molecules for a "
    "clinical topic using ONLY the evidence provided in the user message. "
    "Rules you must follow strictly:\n"
    "1. Never state a clinical claim that is not supported by a provided evidence item; "
    "attach the supporting citation ref_keys to every claim.\n"
    "2. If the provided evidence does not support a section, set insufficient_evidence=true "
    "and say so plainly rather than inventing content.\n"
    "3. Only use citation ref_keys that appear in the provided evidence list.\n"
    "4. Assign GRADE-inspired confidence (high/moderate/low/very_low) per section and row, "
    "and give each comparison row a one-sentence rationale for its confidence.\n"
    "5. Cover these sections where evidence allows: executive_summary, mechanism_of_action, "
    "guidelines, trials, meta_analyses, safety, contraindications, interactions, "
    "special_populations, limitations, evidence_gaps. A 'direct head-to-head comparison' "
    "requires a trial comparing the two molecules against each other, not a review that "
    "merely mentions both."
)


def _cite(docs: list[RankedDoc]) -> list[str]:
    return [d.ref_key for d in docs]


def offline_synthesize(
    molecule_a: str, molecule_b: str, topic: str, verified: list[RankedDoc]
) -> dict:
    """Deterministic extractive synthesis over verified evidence.

    Honors the anti-hallucination contract: claims only assert that a cited
    evidence item exists and is relevant; no clinical conclusions are invented.
    """
    a, b, t = molecule_a, molecule_b, topic
    domains = analyze(a, b, verified)
    h2h = head_to_head(verified, a, b)

    sections: list[dict] = []

    # Executive summary
    if verified:
        summary_claims = [
            {
                "text": (
                    f"{len(verified)} verified evidence item(s) relevant to {t} were "
                    f"retrieved for {a} and {b}; the highest tier present is "
                    f"{top_tier_label(verified).lower()}."
                ),
                "citation_ids": _cite(verified[:3]),
            }
        ]
        if not h2h:
            summary_claims.append(
                {
                    "text": (
                        f"No retrieved trial directly compares {a} and {b} on {t}; "
                        "direct head-to-head evidence is limited."
                    ),
                    "citation_ids": [],
                }
            )
        sections.append(
            {
                "section_key": "executive_summary",
                "title": "Executive Summary",
                "confidence": confidence_from(verified),
                "insufficient_evidence": False,
                "claims": summary_claims,
            }
        )

    # One section per clinical domain, honestly marked insufficient when empty.
    for key in (
        "mechanism_of_action",
        "guidelines",
        "trials",
        "meta_analyses",
        "safety",
        "contraindications",
        "interactions",
        "special_populations",
    ):
        sections.append(_domain_section(domains[key], a, b, t))

    # Limitations — always present, characterizes the evidence base honestly.
    sections.append(
        {
            "section_key": "limitations",
            "title": "Limitations",
            "confidence": "moderate",
            "insufficient_evidence": False,
            "claims": [
                {
                    "text": (
                        "This report characterizes the retrieved, citation-verified evidence "
                        "base; it does not substitute for full appraisal of each source. "
                        f"{grade(verified).rationale}"
                    ),
                    "citation_ids": [],
                }
            ],
        }
    )

    # Evidence gaps — honest about head-to-head.
    sections.append(
        {
            "section_key": "evidence_gaps",
            "title": "Evidence Gaps",
            "confidence": "very_low",
            "insufficient_evidence": not h2h,
            "claims": [
                {
                    "text": (
                        f"A direct head-to-head trial comparing {a} and {b} on {t} "
                        + (
                            "was identified."
                            if h2h
                            else "was NOT identified in the retrieved evidence."
                        )
                    ),
                    "citation_ids": _cite(h2h) if h2h else [],
                }
            ],
        }
    )

    comparison = build_comparison(a, b, t, verified)
    return {
        "sections": sections,
        "comparison": comparison,
        "model_used": "offline-extractive",
        "cost_usd": 0.0,
    }


def _domain_section(dr, a: str, b: str, t: str) -> dict:
    """Build an evidence-characterizing section for one clinical domain."""
    if not dr.docs:
        return {
            "section_key": dr.key,
            "title": dr.title,
            "confidence": "very_low",
            "insufficient_evidence": True,
            "claims": [
                {
                    "text": f"No {dr.title.lower()} evidence was identified for {a} vs {b} on {t}.",
                    "citation_ids": [],
                }
            ],
        }
    claims = [
        {
            "text": (
                f"{d.doc.title} ({d.doc.source}"
                f"{', ' + str(d.doc.publication_year) if d.doc.publication_year else ''}) "
                f"is relevant to {t}."
            ),
            "citation_ids": [d.ref_key],
        }
        for d in dr.docs[:4]
    ]
    claims.append(
        {
            "text": (
                f"Evidence attribution — {a}: {len(dr.a_docs)} item(s); "
                f"{b}: {len(dr.b_docs)} item(s); covering both: {len(dr.shared_docs)}."
            ),
            "citation_ids": _cite(dr.docs[:3]),
        }
    )
    return {
        "section_key": dr.key,
        "title": dr.title,
        "confidence": dr.confidence,
        "insufficient_evidence": False,
        "claims": claims,
    }


async def live_synthesize(
    molecule_a: str, molecule_b: str, topic: str, verified: list[RankedDoc]
) -> dict:
    """Synthesize with Claude (Opus 4.8) using structured outputs. Live-only."""
    import json

    import anthropic  # lazy import so offline/tests don't require the SDK

    settings = get_settings()
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    evidence_lines = [
        f"[{d.ref_key}] {d.doc.title} | source={d.doc.source} | design={d.doc.study_design} "
        f"| year={d.doc.publication_year} | doi={d.doc.doi} | pmid={d.doc.pmid}\n"
        f"    abstract: {d.doc.abstract[:600]}"
        for d in verified
    ]
    user = (
        f"Molecule A: {molecule_a}\nMolecule B: {molecule_b}\nClinical topic: {topic}\n\n"
        f"Verified evidence (cite only these ref_keys):\n" + "\n".join(evidence_lines)
    )

    model = settings.model_synthesis
    with client.messages.stream(
        model=model,
        max_tokens=16000,
        thinking={"type": "adaptive"},
        output_config={
            "effort": "high",
            "format": {"type": "json_schema", "schema": REPORT_SCHEMA},
        },
        system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user}],
    ) as stream:
        message = stream.get_final_message()

    text = next((b.text for b in message.content if getattr(b, "type", None) == "text"), "{}")
    data = json.loads(text)

    valid_refs = {d.ref_key for d in verified}
    _sanitize(data, valid_refs)

    usage = message.usage
    cost = cost_usd(model, usage.input_tokens, usage.output_tokens)
    return {
        "sections": data.get("sections", []),
        "comparison": data.get("comparison", []),
        "model_used": model,
        "cost_usd": cost,
    }


def _sanitize(data: dict, valid_refs: set[str]) -> None:
    """Drop any citation ref_key the model invented (defense in depth)."""
    for section in data.get("sections", []):
        for claim in section.get("claims", []):
            claim["citation_ids"] = [c for c in claim.get("citation_ids", []) if c in valid_refs]
    for row in data.get("comparison", []):
        row["citation_ids"] = [c for c in row.get("citation_ids", []) if c in valid_refs]


async def synthesize(
    molecule_a: str, molecule_b: str, topic: str, verified: list[RankedDoc]
) -> dict:
    settings = get_settings()
    use_live = settings.llm_mode != "offline" and bool(settings.anthropic_api_key)
    if use_live:
        try:
            return await live_synthesize(molecule_a, molecule_b, topic, verified)
        except Exception as exc:  # noqa: BLE001
            log.warning("live synthesis failed, using offline extractive: %s", exc)
    return offline_synthesize(molecule_a, molecule_b, topic, verified)

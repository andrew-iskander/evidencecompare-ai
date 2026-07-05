"""Guideline Agent — summarizes guideline recommendations over retrieved guidelines.

Live: Claude summarizes the recommendation content of the retrieved guideline
documents, closed-book, attaching the guideline's own ref_key to each point.
Offline: deterministic characterization of which guidelines were retrieved and how
they attribute to each molecule. Output is a structured `guideline_summary` the
Medical-Writer agent uses for the report's guidelines section.
"""

from __future__ import annotations

import logging

from app.agents.base import Agent, AgentOutcome, PipelineState
from app.agents.specialists import mentions
from app.core.config import get_settings
from app.llm.client import llm_live_enabled, structured_call
from app.rag.grade import grade
from app.rag.ranking import RankedDoc

log = logging.getLogger("agents.guideline")

_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "text": {"type": "string"},
                    "citation_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["text", "citation_ids"],
            },
        }
    },
    "required": ["claims"],
}

_SYSTEM = (
    "You summarize clinical practice guideline recommendations. Use ONLY the provided "
    "guideline documents. State what each guideline recommends relevant to the two "
    "molecules and topic, attaching that guideline's ref_key to the claim. If the "
    "guidelines do not address a molecule, say so. Never invent a recommendation."
)


def _offline_summary(guidelines: list[RankedDoc], a: str, b: str, t: str) -> dict:
    if not guidelines:
        return {
            "confidence": "very_low",
            "insufficient_evidence": True,
            "claims": [
                {
                    "text": f"No clinical guideline addressing {t} was retrieved for {a} or {b}.",
                    "citation_ids": [],
                }
            ],
        }
    claims = []
    for rd in guidelines:
        which = [m for m in (a, b) if mentions(rd, m)]
        who = ", ".join(which) if which else "the drug class"
        yr = f", {rd.doc.publication_year}" if rd.doc.publication_year else ""
        claims.append(
            {
                "text": (
                    f"{rd.doc.title} ({rd.doc.source}{yr}) provides recommendations "
                    f"relevant to {t}, covering {who}."
                ),
                "citation_ids": [rd.ref_key],
            }
        )
    return {
        "confidence": grade(guidelines).level,
        "insufficient_evidence": False,
        "claims": claims,
    }


class GuidelineAgent(Agent):
    key = "guideline"
    label = "Guideline Agent"
    model = "claude-sonnet-5"

    async def run(self, state: PipelineState) -> AgentOutcome:
        a, b, t = state.molecule_a, state.molecule_b, state.topic
        guidelines = [rd for rd in state.ranked if rd.doc.study_design == "guideline"]
        summary = _offline_summary(guidelines, a, b, t)
        model_used: str | None = None
        in_tok = out_tok = 0
        cost = 0.0

        if guidelines and llm_live_enabled():
            try:
                lines = [
                    f"[{rd.ref_key}] {rd.doc.title} ({rd.doc.source}, "
                    f"{rd.doc.publication_year})\n    {rd.doc.abstract[:700]}"
                    for rd in guidelines
                ]
                res = await structured_call(
                    model=get_settings().model_agent,
                    system=_SYSTEM,
                    user=(
                        f"Molecule A: {a}\nMolecule B: {b}\nTopic: {t}\n\n"
                        "Guidelines:\n" + "\n\n".join(lines)
                    ),
                    schema=_SCHEMA,
                    max_tokens=2000,
                )
                valid = {rd.ref_key for rd in guidelines}
                claims = [
                    {
                        "text": c["text"],
                        "citation_ids": [x for x in c.get("citation_ids", []) if x in valid],
                    }
                    for c in res.data.get("claims", [])
                    if c.get("text")
                ]
                if claims:
                    summary = {
                        "confidence": grade(guidelines).level,
                        "insufficient_evidence": False,
                        "claims": claims,
                    }
                model_used, in_tok, out_tok, cost = (
                    res.model, res.input_tokens, res.output_tokens, res.cost_usd
                )
            except Exception as exc:  # noqa: BLE001
                log.warning("live guideline summary failed, using offline: %s", exc)

        state.guideline_summary = summary
        return AgentOutcome(
            detail=f"{len(guidelines)} guideline(s) summarized",
            model=model_used,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost_usd=cost,
        )

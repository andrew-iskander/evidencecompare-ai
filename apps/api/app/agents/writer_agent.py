"""Medical-Writer Agent — produces the clinician-facing report sections.

Live: Claude Opus synthesizes the narrative sections closed-book over the verified
evidence (via `synthesize`), with the invented-citation sanitizer as defense in
depth. Offline: deterministic extractive synthesis. Either way, the Guideline
agent's structured summary (if produced) replaces the guidelines section, so the
specialists' work flows into the final report.
"""

from __future__ import annotations

from app.agents.base import Agent, AgentOutcome, PipelineState
from app.llm.synthesizer import synthesize


class MedicalWriterAgent(Agent):
    key = "writer"
    label = "Medical-Writer Agent"
    model = "claude-opus-4-8"

    async def run(self, state: PipelineState) -> AgentOutcome:
        a, b, t = state.molecule_a, state.molecule_b, state.topic
        result = await synthesize(a, b, t, state.verified)

        sections = result["sections"]

        # Fold the Guideline agent's richer summary into the guidelines section.
        if state.guideline_summary:
            for section in sections:
                if section.get("section_key") == "guidelines":
                    section["claims"] = state.guideline_summary["claims"]
                    section["confidence"] = state.guideline_summary["confidence"]
                    section["insufficient_evidence"] = state.guideline_summary[
                        "insufficient_evidence"
                    ]
                    break

        state.sections = sections
        if not state.comparison:
            state.comparison = result["comparison"]
        state.synthesis_model = result["model_used"]

        cost = float(result.get("cost_usd", 0.0))
        return AgentOutcome(
            detail=result["model_used"],
            model=result["model_used"],
            cost_usd=cost,
        )

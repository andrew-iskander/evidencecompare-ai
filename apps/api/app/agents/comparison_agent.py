"""Comparison Agent — builds the side-by-side molecule comparison.

Deliberately deterministic: the comparison table characterizes the *verified
evidence base* per molecule (volume, tier, GRADE confidence, head-to-head status)
and never asserts a clinical outcome the retrieved evidence does not support. This
is the same engine used since Phase 4 (`build_comparison`/`molecule_evidence`),
now owned by a named agent in the orchestrator.
"""

from __future__ import annotations

from app.agents.base import Agent, AgentOutcome, PipelineState
from app.pipeline.comparison import build_comparison, molecule_evidence


class ComparisonAgent(Agent):
    key = "comparison"
    label = "Comparison Agent"
    model = "claude-sonnet-5"

    async def run(self, state: PipelineState) -> AgentOutcome:
        a, b, t = state.molecule_a, state.molecule_b, state.topic
        state.comparison = build_comparison(a, b, t, state.verified)
        state.molecule_evidence = molecule_evidence(a, b, state.verified)
        return AgentOutcome(detail=f"{len(state.comparison)} comparison row(s)")

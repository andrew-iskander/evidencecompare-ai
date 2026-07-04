"""AI Orchestrator — coordinates the specialist agents for one report.

Instead of a single model call, the orchestrator runs a chain of specialized
agents, threading a shared `PipelineState` and emitting progress after each:

    Search -> Evidence-Ranking -> Trial-Extraction -> Guideline -> Comparison -> Writer

Each agent has a live-LLM path and a deterministic offline fallback, so the whole
chain runs with or without API keys. The orchestrator owns sequencing, progress
emission, and cost aggregation; persistence stays in the engine.
"""

from __future__ import annotations

import logging

from app.agents.base import Agent, AgentOutcome, PipelineState, Progress, _noop_progress
from app.agents.comparison_agent import ComparisonAgent
from app.agents.extraction_agent import TrialExtractionAgent
from app.agents.guideline_agent import GuidelineAgent
from app.agents.ranking_agent import EvidenceRankingAgent
from app.agents.search_agent import SearchAgent
from app.agents.writer_agent import MedicalWriterAgent

log = logging.getLogger("agents.orchestrator")

# Execution order == display order for the pipeline UI.
DEFAULT_AGENTS: list[Agent] = [
    SearchAgent(),
    EvidenceRankingAgent(),
    TrialExtractionAgent(),
    GuidelineAgent(),
    ComparisonAgent(),
    MedicalWriterAgent(),
]


class AIOrchestrator:
    def __init__(self, agents: list[Agent] | None = None) -> None:
        self.agents = agents if agents is not None else DEFAULT_AGENTS

    async def run(
        self, state: PipelineState, on_progress: Progress = _noop_progress
    ) -> dict[str, AgentOutcome]:
        outcomes: dict[str, AgentOutcome] = {}
        total_cost = 0.0
        for agent in self.agents:
            await on_progress(agent.key, "running", None)
            try:
                outcome = await agent.run(state)
            except Exception as exc:  # noqa: BLE001 - isolate a failing agent
                log.exception("agent %s failed", agent.key)
                outcome = AgentOutcome(detail=f"error: {exc}")
            outcomes[agent.key] = outcome
            total_cost += outcome.cost_usd
            await on_progress(
                agent.key,
                "done",
                outcome.detail,
                cost=outcome.cost_usd,
                input_tokens=outcome.input_tokens,
                output_tokens=outcome.output_tokens,
            )
        state.cost_usd = round(total_cost, 4)
        return outcomes

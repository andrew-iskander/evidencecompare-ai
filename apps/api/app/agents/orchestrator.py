"""AI Orchestrator — coordinates the twelve specialist agents for one report.

The orchestrator receives the request, plans the workflow, assigns work to the
specialist agents, collects their outputs on a shared `PipelineState`, and produces
one final evidence report. It runs the agents in dependency-ordered *stages*;
independent agents within a stage run concurrently. It owns sequencing, per-agent
progress emission, timing, structured execution logs (for the Transparency panel),
and cost aggregation. Persistence stays in the engine.

V3 pipeline (display order = the twelve-agent rail):

    Interpreter → Search → Guideline → Trial-Extraction → Evidence-Ranking →
    Safety → Conflict-Resolution → Citation-Verification → Medical-Writer →
    Visualization → Report-Generator → Continuous-Evidence-Monitor

Data dependencies are honored underneath (e.g. selection/ranking happens in Search;
scoring, safety and conflict read the extractions; verification prunes before the
writer synthesizes), while the rail shows the twelve agents in the spec's order.
"""

from __future__ import annotations

import asyncio
import logging
from time import perf_counter

from app.agents.base import Agent, AgentOutcome, PipelineState, Progress, _noop_progress
from app.agents.conflict_agent import ConflictResolutionAgent
from app.agents.extraction_agent import TrialExtractionAgent
from app.agents.guideline_agent import GuidelineAgent
from app.agents.interpreter_agent import ClinicalQuestionInterpreterAgent
from app.agents.monitor_agent import ContinuousEvidenceMonitorAgent
from app.agents.ranking_agent import EvidenceRankingAgent
from app.agents.report_agent import ReportGeneratorAgent
from app.agents.safety_agent import SafetyAgent
from app.agents.search_agent import SearchAgent
from app.agents.verification_agent import CitationVerificationAgent
from app.agents.visualization_agent import VisualizationAgent
from app.agents.writer_agent import MedicalWriterAgent

log = logging.getLogger("agents.orchestrator")

# Execution plan: a sequence of stages; agents within a stage run concurrently
# (they only read shared state and write disjoint fields — no DB access here).
DEFAULT_PLAN: list[list[Agent]] = [
    [ClinicalQuestionInterpreterAgent()],
    [SearchAgent()],
    [GuidelineAgent(), TrialExtractionAgent()],      # independent: both read `ranked`
    [EvidenceRankingAgent(), SafetyAgent()],         # independent: both read `ranked`+extractions
    [ConflictResolutionAgent()],
    [CitationVerificationAgent()],
    [MedicalWriterAgent()],
    [VisualizationAgent()],
    [ReportGeneratorAgent()],
    [ContinuousEvidenceMonitorAgent()],
]

# Flat display/execution order for the agent rail + roster (12 agents).
DEFAULT_AGENTS: list[Agent] = [a for stage in DEFAULT_PLAN for a in stage]


class AIOrchestrator:
    def __init__(self, plan: list[list[Agent]] | None = None) -> None:
        self.plan = plan if plan is not None else DEFAULT_PLAN
        self.agents = [a for stage in self.plan for a in stage]

    async def _run_agent(
        self, agent: Agent, state: PipelineState
    ) -> tuple[Agent, AgentOutcome, float]:
        start = perf_counter()
        try:
            outcome = await agent.run(state)
        except Exception as exc:  # noqa: BLE001 - isolate a failing agent
            log.exception("agent %s failed", agent.key)
            outcome = AgentOutcome(detail=f"error: {exc}")
        ms = round((perf_counter() - start) * 1000, 1)
        return agent, outcome, ms

    async def run(
        self, state: PipelineState, on_progress: Progress = _noop_progress
    ) -> dict[str, AgentOutcome]:
        outcomes: dict[str, AgentOutcome] = {}
        total_cost = 0.0

        for stage in self.plan:
            # Mark every agent in the stage running (sequential DB-safe emission).
            for agent in stage:
                await on_progress(agent.key, "running", None)

            # Run the stage; a single-agent stage still goes through gather.
            results = await asyncio.gather(
                *(self._run_agent(agent, state) for agent in stage)
            )

            for agent, outcome, ms in results:
                outcomes[agent.key] = outcome
                total_cost += outcome.cost_usd
                state.timings[agent.key] = ms
                errored = outcome.detail.startswith("error:")
                state.logs.append(
                    {
                        "agent": agent.key,
                        "label": agent.label,
                        "model": outcome.model or agent.model,
                        "state": "error" if errored else "done",
                        "detail": outcome.detail,
                        "cost_usd": round(outcome.cost_usd, 4),
                        "input_tokens": outcome.input_tokens,
                        "output_tokens": outcome.output_tokens,
                        "ms": ms,
                    }
                )
                await on_progress(
                    agent.key,
                    "error" if errored else "done",
                    outcome.detail,
                    cost=outcome.cost_usd,
                    input_tokens=outcome.input_tokens,
                    output_tokens=outcome.output_tokens,
                )

        state.cost_usd = round(total_cost, 4)
        return outcomes

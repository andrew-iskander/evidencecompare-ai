"""Foundations for the multi-agent evidence orchestrator.

Each specialist agent (Search, Guideline, Trial-Extraction, Evidence-Ranking,
Comparison, Medical-Writer) is a small object with one `run(state)` coroutine.
Agents read and mutate a shared `PipelineState`, emit progress, and return an
`AgentOutcome` (detail + token/cost accounting). Every agent has a live-LLM path
guarded by `llm_live_enabled()` and a deterministic offline fallback, so the whole
pipeline runs and is testable with no network or API keys.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from app.evidence.base import EvidenceSource, RawDoc
from app.rag.ranking import RankedDoc

# emit(agent_key, state, detail, *, cost, input_tokens, output_tokens) -> awaitable.
# Extra keyword accounting is optional so simple emitters can ignore it.
Progress = Callable[..., Awaitable[None]]


async def _noop_progress(
    agent: str, state: str, detail: str | None = None, **_: Any
) -> None:
    return None


@dataclass
class PipelineState:
    """Mutable state threaded through the agent chain for a single report."""

    molecule_a: str
    molecule_b: str
    topic: str

    # Optional explicit evidence sources (tests inject these for determinism).
    sources: list[EvidenceSource] | None = None

    # Search agent
    queries: list[str] = field(default_factory=list)
    raw_docs: list[RawDoc] = field(default_factory=list)

    # Ranking agent
    ranked: list[RankedDoc] = field(default_factory=list)
    verified: list[RankedDoc] = field(default_factory=list)

    # Clinical-question interpreter (PICO + expanded search terms)
    research_plan: dict | None = None

    # Trial-extraction agent (structured per-study records)
    extractions: list[dict] = field(default_factory=list)

    # Guideline agent
    guideline_summary: dict | None = None

    # Evidence-ranking (scoring) agent: overall + per-study quality scores
    scores: dict = field(default_factory=dict)

    # Safety agent: comparative safety matrix
    safety_matrix: dict | None = None

    # Conflict-resolution agent: evidence reconciliation summary
    reconciliation: dict | None = None
    conflicts: list[str] = field(default_factory=list)

    # Citation-verification agent: verification report (checked/broken/removed)
    verification: dict = field(default_factory=dict)

    # Comparison + writer agents
    comparison: list[dict] = field(default_factory=list)
    sections: list[dict] = field(default_factory=list)
    molecule_evidence: dict = field(default_factory=dict)

    # Visualization agent: precomputed payloads for the frontend charts
    visualizations: dict = field(default_factory=dict)

    # Continuous-evidence monitor: living-evidence fingerprint + freshness verdict
    fingerprint: list[str] = field(default_factory=list)
    freshness: str = "unknown"

    # Provenance / transparency
    synthesis_model: str = "offline-extractive"
    cost_usd: float = 0.0
    snapshot: dict = field(default_factory=dict)
    # Orchestrator execution logs (one structured entry per agent) + timings (ms).
    logs: list[dict] = field(default_factory=list)
    timings: dict[str, float] = field(default_factory=dict)


@dataclass
class AgentOutcome:
    """What an agent reports back to the orchestrator for progress + accounting."""

    detail: str
    model: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0


class Agent:
    """Base specialist agent. Subclasses implement `run`."""

    key: str = "agent"
    label: str = "Agent"
    model: str | None = None

    async def run(self, state: PipelineState) -> AgentOutcome:  # pragma: no cover
        raise NotImplementedError

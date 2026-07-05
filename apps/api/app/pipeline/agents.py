"""Agent roster for the multi-agent evidence orchestrator (V3).

Keys and order match `app.agents.orchestrator.DEFAULT_AGENTS`; the pipeline
pre-creates one AgentRun row per entry (pending) so the UI shows the full
twelve-agent pipeline before work starts, then the orchestrator advances each.
"""

from __future__ import annotations

from app.agents.orchestrator import DEFAULT_AGENTS

# (key, label, model tier). Order == execution + display order. Derived from the
# orchestrator's agent list so the roster can never drift out of sync with it.
AGENT_ROSTER: list[tuple[str, str, str]] = [
    (a.key, a.label, a.model or "deterministic") for a in DEFAULT_AGENTS
]

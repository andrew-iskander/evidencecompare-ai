"""Agent roster for the multi-agent evidence orchestrator.

Keys and order match `app.agents.orchestrator.DEFAULT_AGENTS`; the pipeline
pre-creates one AgentRun row per entry (pending) so the UI shows the full
six-agent pipeline before work starts, then the orchestrator advances each.
"""

from __future__ import annotations

# (key, label, model tier). Order == execution + display order.
AGENT_ROSTER: list[tuple[str, str, str]] = [
    ("search", "Search Agent", "claude-sonnet-5"),
    ("ranking", "Evidence-Ranking Agent", "claude-haiku-4-5"),
    ("extraction", "Trial-Extraction Agent", "claude-haiku-4-5"),
    ("guideline", "Guideline Agent", "claude-sonnet-5"),
    ("comparison", "Comparison Agent", "claude-sonnet-5"),
    ("writer", "Medical-Writer Agent", "claude-opus-4-8"),
]

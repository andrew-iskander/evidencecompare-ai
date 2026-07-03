"""Static agent roster for the evidence pipeline.

Phase 2 wires the orchestration and per-agent progress reporting. The agents
themselves are stubs here — the real RAG-backed agents land in Phase 3.
"""

from __future__ import annotations

# (key, label, model tier). Cost is illustrative for Phase 2 accounting.
AGENT_ROSTER: list[tuple[str, str, str]] = [
    ("search", "Search", "claude-sonnet-5"),
    ("guideline", "Guidelines", "claude-sonnet-5"),
    ("trial", "Trials", "claude-sonnet-5"),
    ("meta_analysis", "Meta-analyses", "claude-sonnet-5"),
    ("safety", "Safety", "claude-sonnet-5"),
    ("ranking", "Evidence ranking", "claude-haiku-4-5"),
    ("verification", "Citation verification", "claude-haiku-4-5"),
    ("report", "Report generation", "claude-opus-4-8"),
]

"""Continuous-Evidence Monitor — establishes the living-evidence baseline.

At report time this agent records the retrieval fingerprint (dedup keys of every
candidate) and the categories it will watch — new RCTs, updated meta-analyses,
updated guidelines, and new FDA/EMA safety communications. The ongoing sweep
(`services.freshness_service` + the Celery beat task) later re-runs retrieval for a
completed report, diffs against this fingerprint, and flags the report
`update_available` when significant new high-tier evidence appears — which is how
users are notified their report has become outdated.
"""

from __future__ import annotations

from app.agents.base import Agent, AgentOutcome, PipelineState

# High-tier arrivals the monitor treats as "report is now outdated" signals.
_WATCHED = [
    "new randomized controlled trials",
    "updated meta-analyses / systematic reviews",
    "updated clinical guidelines",
    "new FDA safety communications",
    "new EMA safety communications",
]


class ContinuousEvidenceMonitorAgent(Agent):
    key = "monitor"
    label = "Continuous-Evidence Monitor"
    model = "claude-haiku-4-5"

    async def run(self, state: PipelineState) -> AgentOutcome:
        fingerprint = sorted({d.dedup_key() for d in state.raw_docs})
        state.fingerprint = fingerprint
        state.freshness = "up_to_date"
        state.snapshot["monitor"] = {
            "fingerprint_size": len(fingerprint),
            "watched": _WATCHED,
        }
        return AgentOutcome(
            detail=(
                f"baseline fingerprint set ({len(fingerprint)} items); "
                f"monitoring {len(_WATCHED)} signal types"
            )
        )

"""Living-evidence detection.

Re-runs retrieval for a completed report's query and compares the current
candidate set against the report's stored fingerprint. If newer high-tier
evidence (RCT, meta-analysis, systematic review, guideline, registered trial)
has appeared, the report is flagged `update_available`; otherwise `up_to_date`.

Offline mode uses static fixtures, so the fingerprint matches and reports stay
`up_to_date` — honest, since no new evidence actually exists offline.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.evidence.base import EvidenceSource, RawDoc
from app.evidence.registry import retrieve_evidence
from app.models.report import Report

log = logging.getLogger("services.freshness")

# Tiers whose arrival should trigger an "update available" flag.
_SIGNIFICANT = {"rct", "meta_analysis", "systematic_review", "guideline", "trial_registry"}


def significant_new(prev_keys: set[str], docs: list[RawDoc]) -> list[RawDoc]:
    """High-tier docs present now but absent from the report's fingerprint."""
    seen: set[str] = set()
    out: list[RawDoc] = []
    for d in docs:
        key = d.dedup_key()
        if key in prev_keys or key in seen or d.study_design not in _SIGNIFICANT:
            continue
        seen.add(key)
        out.append(d)
    return out


async def check_updates(
    db: AsyncSession, report: Report, sources: list[EvidenceSource] | None = None
) -> dict:
    """Check for newer evidence and persist the freshness verdict on the report."""
    docs = await retrieve_evidence(
        report.molecule_a, report.molecule_b, report.topic, sources=sources
    )
    prev = set(report.evidence_fingerprint or [])
    new_significant = significant_new(prev, docs)

    status = "update_available" if new_significant else "up_to_date"
    report.freshness = status
    report.freshness_checked_at = datetime.now(UTC)
    await db.commit()

    return {
        "status": status,
        "new_items": len(new_significant),
        "checked_at": report.freshness_checked_at,
        "details": [
            f"{d.study_design or 'study'}: {d.title}"[:200] for d in new_significant[:8]
        ],
    }

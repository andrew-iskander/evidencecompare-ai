from __future__ import annotations

import asyncio
import uuid

from app.pipeline.orchestrator import run_pipeline
from app.workers.celery_app import celery_app


@celery_app.task(name="run_report")
def run_report_task(report_id: str) -> str:
    """Celery entrypoint for the evidence pipeline (PIPELINE_MODE=celery)."""
    asyncio.run(run_pipeline(uuid.UUID(report_id)))
    return report_id


async def _scan_stale_reports() -> int:
    """Living evidence: re-check freshness of complete reports not checked recently."""
    from datetime import UTC, datetime, timedelta

    from sqlalchemy import or_, select

    from app.core.config import get_settings
    from app.db.session import AsyncSessionLocal
    from app.models.report import Report
    from app.services.freshness_service import check_updates

    cutoff = datetime.now(UTC) - timedelta(hours=get_settings().freshness_stale_hours)
    checked = 0
    async with AsyncSessionLocal() as db:
        stale = await db.scalars(
            select(Report).where(
                Report.status == "complete",
                or_(Report.freshness_checked_at.is_(None), Report.freshness_checked_at < cutoff),
            )
        )
        for report in list(stale):
            await check_updates(db, report)
            checked += 1
    return checked


@celery_app.task(name="scan_stale_reports")
def scan_stale_reports_task() -> int:
    """Periodic living-evidence sweep (enable via Celery beat; see celery_app)."""
    return asyncio.run(_scan_stale_reports())

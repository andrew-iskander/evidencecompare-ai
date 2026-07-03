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

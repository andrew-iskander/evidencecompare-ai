"""Evidence pipeline orchestrator.

Creates the agent-run rows for progress reporting and drives the RAG evidence
engine (Phase 3), updating each agent's state as the engine advances so the SSE
stream reflects real work.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.models.report import AgentRun, Report
from app.pipeline.agents import AGENT_ROSTER
from app.pipeline.engine import run_engine

log = logging.getLogger("pipeline")


def _now() -> datetime:
    return datetime.now(UTC)


async def run_pipeline(report_id: uuid.UUID) -> None:
    settings = get_settings()
    delay = settings.pipeline_step_delay

    async with AsyncSessionLocal() as db:
        report = await db.get(Report, report_id)
        if report is None:
            log.warning("run_pipeline: report %s not found", report_id)
            return
        try:
            report.status = "running"
            await db.commit()

            # Pre-create agent-run rows (pending) so the UI shows the full pipeline.
            runs: dict[str, AgentRun] = {}
            for idx, (key, label, model) in enumerate(AGENT_ROSTER):
                run = AgentRun(
                    report_id=report.id,
                    agent=key,
                    label=label,
                    model=model,
                    state="pending",
                    order_index=idx,
                )
                db.add(run)
                runs[key] = run
            await db.commit()

            async def on_progress(agent: str, state: str, detail: str | None = None) -> None:
                run = runs.get(agent)
                if run is None:
                    return
                if state == "running":
                    run.state = "running"
                    run.started_at = _now()
                elif state == "done":
                    run.state = "done"
                    run.detail = detail
                    run.ended_at = _now()
                await db.commit()
                if delay and state == "running":
                    await asyncio.sleep(delay)

            summary = await run_engine(db, report, on_progress=on_progress)

            report.status = "complete"
            report.completed_at = _now()
            report.token_cost_usd = round(float(summary.get("cost_usd", 0.0)), 4)
            await db.commit()
            log.info(
                "run_pipeline: report %s complete (%s candidates, %s verified, $%.4f)",
                report_id,
                summary.get("candidates"),
                summary.get("verified"),
                summary.get("cost_usd", 0.0),
            )

        except Exception as exc:  # noqa: BLE001
            log.exception("run_pipeline failed for %s", report_id)
            await db.rollback()
            report = await db.get(Report, report_id)
            if report is not None:
                report.status = "failed"
                report.error = str(exc)
                await db.commit()


async def dispatch_pipeline(report_id: uuid.UUID) -> None:
    """Dispatch the pipeline according to PIPELINE_MODE."""
    mode = get_settings().pipeline_mode
    if mode == "eager":
        await run_pipeline(report_id)
    elif mode == "celery":
        from app.workers.tasks import run_report_task

        run_report_task.delay(str(report_id))
    else:  # background
        asyncio.create_task(run_pipeline(report_id))

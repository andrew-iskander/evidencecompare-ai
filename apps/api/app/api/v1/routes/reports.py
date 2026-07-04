from __future__ import annotations

import asyncio
import json
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, user_from_query_token
from app.core.config import get_settings
from app.db.session import AsyncSessionLocal, get_db
from app.models.user import User
from app.pipeline.orchestrator import dispatch_pipeline
from app.schemas.report import (
    FreshnessOut,
    ReportCreateIn,
    ReportOut,
    ReportSummary,
    ShareOut,
)
from app.services import freshness_service, report_service

router = APIRouter(prefix="/reports", tags=["reports"])


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def _start_report(db: AsyncSession, user: User, data: ReportCreateIn) -> ReportOut:
    report = await report_service.create_report(db, user, data)
    await dispatch_pipeline(report.id)
    fresh = await report_service.get_report_full(db, report.id)
    return ReportOut.from_report(fresh)


@router.post("", response_model=ReportOut, status_code=status.HTTP_202_ACCEPTED)
async def create_report(
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReportOut:
    data = ReportCreateIn.model_validate(body)

    # Cache: reuse a recent complete report for the same query unless refresh=true.
    if not data.refresh:
        ttl = get_settings().report_cache_ttl_hours
        key = report_service.normalize_query_key(
            data.molecule_a, data.molecule_b, data.topic
        )
        cached = await report_service.find_cached_report(db, user, key, ttl)
        if cached is not None:
            return ReportOut.from_report(cached, cached=True)

    return await _start_report(db, user, data)


@router.post(
    "/{report_id}/refresh",
    response_model=ReportOut,
    status_code=status.HTTP_202_ACCEPTED,
)
async def refresh_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReportOut:
    """Manual refresh: run a fresh evidence report from the same inputs."""
    src = await report_service.get_owned_report(db, report_id, user)
    data = ReportCreateIn(
        molecule_a=src.molecule_a,
        molecule_b=src.molecule_b,
        topic=src.topic,
        options=src.inputs or {},
        refresh=True,
    )
    return await _start_report(db, user, data)


@router.post("/{report_id}/check-updates", response_model=FreshnessOut)
async def check_updates(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FreshnessOut:
    """Living evidence: detect newer high-tier evidence since this report ran."""
    report = await report_service.get_owned_report(db, report_id, user)
    result = await freshness_service.check_updates(db, report)
    return FreshnessOut(**result)


@router.get("", response_model=list[ReportSummary])
async def list_my_reports(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ReportSummary]:
    reports = await report_service.list_reports(db, user)
    return [ReportSummary.model_validate(r) for r in reports]


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReportOut:
    report = await report_service.get_owned_report(db, report_id, user)
    return ReportOut.from_report(report)


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    report = await report_service.get_owned_report(db, report_id, user)
    await report_service.delete_report(db, report)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{report_id}/share", response_model=ShareOut)
async def share_report(
    report_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ShareOut:
    report = await report_service.get_owned_report(db, report_id, user)
    token = await report_service.make_share_token(db, report)
    base = str(request.base_url).rstrip("/")
    return ShareOut(share_token=token, url=f"{base}/api/v1/reports/{report_id}?share={token}")


async def _event_stream(report_id: uuid.UUID) -> AsyncIterator[str]:
    last_status: str | None = None
    seen_agents: dict[str, str] = {}
    sent_sections: set[str] = set()

    for _ in range(600):  # safety bound (~4 min at 0.4s)
        async with AsyncSessionLocal() as db:
            report = await report_service.get_report_full(db, report_id)
        if report is None:
            yield _sse("error", {"message": "report not found"})
            return

        if report.status != last_status:
            last_status = report.status
            yield _sse("status", {"status": report.status})

        for run in report.agent_runs:
            if seen_agents.get(run.agent) != run.state:
                seen_agents[run.agent] = run.state
                yield _sse(
                    "agent",
                    {"agent": run.agent, "label": run.label, "state": run.state},
                )

        for section in report.sections:
            if section.section_key not in sent_sections:
                sent_sections.add(section.section_key)
                yield _sse(
                    "section",
                    {"section_key": section.section_key, "confidence": section.confidence},
                )

        if report.status == "complete":
            yield _sse(
                "complete",
                {"report_id": str(report.id), "cost_usd": float(report.token_cost_usd or 0)},
            )
            return
        if report.status == "failed":
            yield _sse("error", {"message": report.error or "pipeline failed"})
            return

        await asyncio.sleep(0.4)

    yield _sse("error", {"message": "stream timed out"})


@router.get("/{report_id}/stream")
async def stream_report(
    report_id: uuid.UUID,
    token: str = Query(..., description="Access token (EventSource cannot set headers)"),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    user = await user_from_query_token(token, db)
    await report_service.get_owned_report(db, report_id, user)  # authorize
    return StreamingResponse(
        _event_stream(report_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

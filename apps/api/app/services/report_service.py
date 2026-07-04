from __future__ import annotations

import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.report import Report
from app.models.user import User
from app.schemas.report import ReportCreateIn


def normalize_query_key(molecule_a: str, molecule_b: str, topic: str) -> str:
    """Case/whitespace-insensitive cache key. A/B order is preserved (it drives
    the report's column assignment), so 'A vs B' and 'B vs A' are distinct."""
    def norm(s: str) -> str:
        return " ".join(s.lower().split())

    return f"{norm(molecule_a)}|{norm(molecule_b)}|{norm(topic)}"

_FULL = (
    selectinload(Report.sections),
    selectinload(Report.comparison_rows),
    selectinload(Report.citations),
    selectinload(Report.extractions),
    selectinload(Report.agent_runs),
)


async def create_report(db: AsyncSession, user: User, data: ReportCreateIn) -> Report:
    report = Report(
        user_id=user.id,
        molecule_a=data.molecule_a,
        molecule_b=data.molecule_b,
        topic=data.topic,
        query_key=normalize_query_key(data.molecule_a, data.molecule_b, data.topic),
        inputs=data.options,
        status="queued",
        freshness="unknown",
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


async def find_cached_report(
    db: AsyncSession, user: User, query_key: str, ttl_hours: int
) -> Report | None:
    """Most recent COMPLETE report for this user + query within the cache window."""
    cutoff = datetime.now(UTC) - timedelta(hours=ttl_hours)
    return await db.scalar(
        select(Report)
        .where(
            Report.user_id == user.id,
            Report.query_key == query_key,
            Report.status == "complete",
            Report.created_at >= cutoff,
        )
        .order_by(Report.created_at.desc())
        .options(*_FULL)
    )


async def get_report_full(db: AsyncSession, report_id: uuid.UUID) -> Report | None:
    return await db.scalar(
        select(Report).where(Report.id == report_id).options(*_FULL)
    )


async def get_owned_report(
    db: AsyncSession, report_id: uuid.UUID, user: User
) -> Report:
    report = await get_report_full(db, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if report.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    return report


async def list_reports(db: AsyncSession, user: User) -> list[Report]:
    result = await db.scalars(
        select(Report)
        .where(Report.user_id == user.id)
        .order_by(Report.created_at.desc())
    )
    return list(result)


async def delete_report(db: AsyncSession, report: Report) -> None:
    await db.delete(report)
    await db.commit()


async def make_share_token(db: AsyncSession, report: Report) -> str:
    if not report.share_token:
        report.share_token = secrets.token_urlsafe(16)
        await db.commit()
    return report.share_token

from __future__ import annotations

import secrets
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.report import Report
from app.models.user import User
from app.schemas.report import ReportCreateIn

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
        inputs=data.options,
        status="queued",
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


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

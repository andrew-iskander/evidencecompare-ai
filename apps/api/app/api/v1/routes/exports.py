from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.report import Export
from app.models.user import User
from app.schemas.export import ExportCreateIn, ExportFormat, ExportOut
from app.services import report_service
from app.services.export_service import build_export, render_export

router = APIRouter(tags=["exports"])


@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: uuid.UUID,
    format: ExportFormat,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Response:
    """Generate and return a report file (markdown/pdf/xlsx/pptx) for download."""
    report = await report_service.get_owned_report(db, report_id, user)
    if report.status != "complete":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Report is not complete yet"
        )
    data, media_type, filename = render_export(report, format)
    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post(
    "/reports/{report_id}/exports",
    response_model=ExportOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_export(
    report_id: uuid.UUID,
    data: ExportCreateIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Export:
    report = await report_service.get_owned_report(db, report_id, user)
    if report.status != "complete":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Report is not complete yet",
        )
    export = build_export(report, data.format)
    db.add(export)
    await db.commit()
    await db.refresh(export)
    return export


@router.get("/exports/{export_id}", response_model=ExportOut)
async def get_export(
    export_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Export:
    export = await db.get(Export, export_id)
    if export is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export not found")
    # ownership via the parent report
    await report_service.get_owned_report(db, export.report_id, user)
    return export

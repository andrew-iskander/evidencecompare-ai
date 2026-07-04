"""add section transparency layer + report conflicts

Revision ID: 4c7e3d9a1b23
Revises: 3b6d2c8f0a12
Create Date: 2026-07-04

Adds report_sections.layer (retrieved_evidence | ai_interpretation |
clinical_summary) and reports.conflicts (quality-control conflict notes).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "4c7e3d9a1b23"
down_revision: str | None = "3b6d2c8f0a12"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "report_sections",
        sa.Column(
            "layer",
            sa.String(length=24),
            nullable=False,
            server_default="ai_interpretation",
        ),
    )
    op.add_column("reports", sa.Column("conflicts", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("reports", "conflicts")
    op.drop_column("report_sections", "layer")

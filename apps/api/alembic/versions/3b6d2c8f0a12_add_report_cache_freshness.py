"""add report caching + living-evidence columns

Revision ID: 3b6d2c8f0a12
Revises: 2a5c1b7e9f01
Create Date: 2026-07-04

Adds query_key (cache/grouping), freshness + freshness_checked_at (living evidence),
and evidence_fingerprint (retrieval snapshot for update detection) to reports.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "3b6d2c8f0a12"
down_revision: str | None = "2a5c1b7e9f01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("reports", sa.Column("query_key", sa.String(length=1024), nullable=True))
    op.add_column(
        "reports",
        sa.Column("freshness", sa.String(length=24), nullable=False, server_default="unknown"),
    )
    op.add_column(
        "reports", sa.Column("freshness_checked_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column("reports", sa.Column("evidence_fingerprint", sa.JSON(), nullable=True))
    op.create_index(op.f("ix_reports_query_key"), "reports", ["query_key"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_reports_query_key"), table_name="reports")
    op.drop_column("reports", "evidence_fingerprint")
    op.drop_column("reports", "freshness_checked_at")
    op.drop_column("reports", "freshness")
    op.drop_column("reports", "query_key")

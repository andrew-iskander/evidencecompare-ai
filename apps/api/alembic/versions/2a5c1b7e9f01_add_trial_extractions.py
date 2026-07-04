"""add trial_extractions table

Revision ID: 2a5c1b7e9f01
Revises: 1e97fd1330a4
Create Date: 2026-07-04

Adds structured per-study extraction records produced by the Trial-Extraction
agent (multi-agent orchestrator upgrade).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "2a5c1b7e9f01"
down_revision: str | None = "1e97fd1330a4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "trial_extractions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("report_id", sa.Uuid(), nullable=False),
        sa.Column("doc_id", sa.Uuid(), nullable=True),
        sa.Column("ref_key", sa.String(length=16), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("study_design", sa.String(length=48), nullable=True),
        sa.Column("population", sa.Text(), nullable=True),
        sa.Column("intervention", sa.Text(), nullable=True),
        sa.Column("comparator", sa.Text(), nullable=True),
        sa.Column("sample_size", sa.Integer(), nullable=True),
        sa.Column("outcomes", sa.JSON(), nullable=False),
        sa.Column("hazard_ratio", sa.String(length=128), nullable=True),
        sa.Column("relative_risk", sa.String(length=128), nullable=True),
        sa.Column("confidence_interval", sa.String(length=128), nullable=True),
        sa.Column("p_value", sa.String(length=64), nullable=True),
        sa.Column("adverse_events", sa.JSON(), nullable=False),
        sa.Column("strengths", sa.JSON(), nullable=False),
        sa.Column("limitations", sa.JSON(), nullable=False),
        sa.Column("extractor_model", sa.String(length=64), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["doc_id"], ["evidence_docs.id"]),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_trial_extractions_report_id"),
        "trial_extractions",
        ["report_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_trial_extractions_report_id"), table_name="trial_extractions")
    op.drop_table("trial_extractions")

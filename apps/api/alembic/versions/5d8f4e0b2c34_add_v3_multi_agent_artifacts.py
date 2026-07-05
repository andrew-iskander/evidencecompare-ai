"""add V3 multi-agent report artifacts

Revision ID: 5d8f4e0b2c34
Revises: 4c7e3d9a1b23
Create Date: 2026-07-05

Adds the nullable JSON columns the V3 twelve-agent orchestrator persists on a
report: the interpreter's research plan, evidence scores, the safety matrix, the
conflict reconciliation, precomputed visualizations, the citation-verification
report, and the orchestrator's execution logs + per-agent timings. All are nullable
so existing V2 reports remain valid (backward compatible).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "5d8f4e0b2c34"
down_revision: str | None = "4c7e3d9a1b23"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_COLUMNS = [
    "research_plan",
    "evidence_scores",
    "safety_matrix",
    "reconciliation",
    "visualizations",
    "verification",
    "agent_logs",
    "agent_timings",
]


def upgrade() -> None:
    for name in _COLUMNS:
        op.add_column("reports", sa.Column(name, sa.JSON(), nullable=True))


def downgrade() -> None:
    for name in reversed(_COLUMNS):
        op.drop_column("reports", name)

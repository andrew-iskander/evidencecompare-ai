from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _now() -> datetime:
    return datetime.now(UTC)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=True
    )
    molecule_a: Mapped[str] = mapped_column(String(255))
    molecule_b: Mapped[str] = mapped_column(String(255))
    topic: Mapped[str] = mapped_column(String(512))
    # Normalized cache key "a|b|topic" for reuse + living-evidence grouping.
    query_key: Mapped[str | None] = mapped_column(String(1024), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(32), default="queued", index=True)
    inputs: Mapped[dict] = mapped_column(JSON, default=dict)
    # Living evidence: up_to_date | update_available | unknown, plus the retrieval
    # fingerprint (dedup keys of candidates) used to detect newer evidence.
    freshness: Mapped[str] = mapped_column(String(24), default="unknown")
    freshness_checked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    evidence_fingerprint: Mapped[list] = mapped_column(JSON, default=list)
    # Quality control: human-readable notes where retrieved evidence conflicts.
    conflicts: Mapped[list] = mapped_column(JSON, default=list)
    model_synthesis: Mapped[str | None] = mapped_column(String(64), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    # Per-molecule evidence counts by macro-domain, for the risk-benefit matrix.
    molecule_evidence: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    token_cost_usd: Mapped[float] = mapped_column(Numeric(10, 4), default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    share_token: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    sections: Mapped[list[ReportSection]] = relationship(
        back_populates="report", cascade="all, delete-orphan", order_by="ReportSection.order_index"
    )
    comparison_rows: Mapped[list[ComparisonRow]] = relationship(
        back_populates="report", cascade="all, delete-orphan", order_by="ComparisonRow.order_index"
    )
    citations: Mapped[list[Citation]] = relationship(
        back_populates="report", cascade="all, delete-orphan", order_by="Citation.order_index"
    )
    extractions: Mapped[list[TrialExtraction]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="TrialExtraction.order_index",
    )
    agent_runs: Mapped[list[AgentRun]] = relationship(
        back_populates="report", cascade="all, delete-orphan", order_by="AgentRun.order_index"
    )
    exports: Mapped[list[Export]] = relationship(
        back_populates="report", cascade="all, delete-orphan"
    )


class ReportSection(Base):
    __tablename__ = "report_sections"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("reports.id", ondelete="CASCADE"), index=True
    )
    section_key: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(255))
    # Transparency layer: retrieved_evidence | ai_interpretation | clinical_summary.
    layer: Mapped[str] = mapped_column(String(24), default="ai_interpretation")
    confidence: Mapped[str] = mapped_column(String(16), default="moderate")
    insufficient_evidence: Mapped[bool] = mapped_column(Boolean, default=False)
    claims: Mapped[list] = mapped_column(JSON, default=list)  # [{text, citation_ids:[]}]
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    report: Mapped[Report] = relationship(back_populates="sections")


class ComparisonRow(Base):
    __tablename__ = "comparison_rows"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("reports.id", ondelete="CASCADE"), index=True
    )
    attribute: Mapped[str] = mapped_column(String(255))
    value_a: Mapped[str] = mapped_column(Text)
    value_b: Mapped[str] = mapped_column(Text)
    confidence: Mapped[str] = mapped_column(String(16), default="moderate")
    rationale: Mapped[str | None] = mapped_column(Text, nullable=True)
    citation_ids: Mapped[list] = mapped_column(JSON, default=list)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    report: Mapped[Report] = relationship(back_populates="comparison_rows")


class EvidenceDoc(Base):
    """Retrieved source record. Vector columns + chunks are added in Phase 3 (pgvector)."""

    __tablename__ = "evidence_docs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(32))
    external_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    doi: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    pmid: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    study_design: Mapped[str | None] = mapped_column(String(48), nullable=True)
    publication_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sample_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    doc_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class DocChunk(Base):
    """A chunk of an evidence document plus its embedding.

    Phase 3 stores embeddings as JSON for cross-database portability (SQLite dev,
    Postgres prod). In production this column is replaced by a pgvector `vector`
    column + HNSW index; retrieval then uses SQL ANN instead of Python cosine.
    """

    __tablename__ = "doc_chunks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    doc_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("evidence_docs.id", ondelete="CASCADE"), index=True
    )
    report_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("reports.id", ondelete="CASCADE"), index=True, nullable=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list] = mapped_column(JSON, default=list)


class Citation(Base):
    __tablename__ = "citations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("reports.id", ondelete="CASCADE"), index=True
    )
    doc_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("evidence_docs.id"), nullable=True
    )
    ref_key: Mapped[str] = mapped_column(String(16))  # stable per-report id, e.g. "c1"
    title: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(32))
    study_design: Mapped[str | None] = mapped_column(String(48), nullable=True)
    doi: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pmid: Mapped[str | None] = mapped_column(String(32), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    locator: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    report: Mapped[Report] = relationship(back_populates="citations")


class TrialExtraction(Base):
    """Structured data extracted from one retrieved study by the Trial-Extraction agent.

    Numeric effect measures are stored as strings to preserve source fidelity
    (e.g. "HR 0.86 (95% CI 0.74-0.99)"); list-valued fields are JSON. Every row is
    tied to a verified citation via `ref_key`, so nothing here is uncited.
    """

    __tablename__ = "trial_extractions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("reports.id", ondelete="CASCADE"), index=True
    )
    doc_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("evidence_docs.id"), nullable=True
    )
    ref_key: Mapped[str] = mapped_column(String(16))  # matches the citation ref_key
    title: Mapped[str] = mapped_column(Text)
    study_design: Mapped[str | None] = mapped_column(String(48), nullable=True)
    population: Mapped[str | None] = mapped_column(Text, nullable=True)
    intervention: Mapped[str | None] = mapped_column(Text, nullable=True)
    comparator: Mapped[str | None] = mapped_column(Text, nullable=True)
    sample_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    outcomes: Mapped[list] = mapped_column(JSON, default=list)  # [str]
    hazard_ratio: Mapped[str | None] = mapped_column(String(128), nullable=True)
    relative_risk: Mapped[str | None] = mapped_column(String(128), nullable=True)
    confidence_interval: Mapped[str | None] = mapped_column(String(128), nullable=True)
    p_value: Mapped[str | None] = mapped_column(String(64), nullable=True)
    adverse_events: Mapped[list] = mapped_column(JSON, default=list)  # [str]
    strengths: Mapped[list] = mapped_column(JSON, default=list)  # [str]
    limitations: Mapped[list] = mapped_column(JSON, default=list)  # [str]
    extractor_model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)

    report: Mapped[Report] = relationship(back_populates="extractions")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("reports.id", ondelete="CASCADE"), index=True
    )
    agent: Mapped[str] = mapped_column(String(48))
    label: Mapped[str] = mapped_column(String(64))
    model: Mapped[str | None] = mapped_column(String(64), nullable=True)
    state: Mapped[str] = mapped_column(String(16), default="pending")  # pending|running|done|error
    detail: Mapped[str | None] = mapped_column(String(255), nullable=True)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Numeric(10, 4), default=0)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    report: Mapped[Report] = relationship(back_populates="agent_runs")


class Export(Base):
    __tablename__ = "exports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    report_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("reports.id", ondelete="CASCADE"), index=True
    )
    format: Mapped[str] = mapped_column(String(16))  # pdf|pptx|xlsx|markdown
    status: Mapped[str] = mapped_column(String(16), default="processing")
    object_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)  # inline for markdown
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    report: Mapped[Report] = relationship(back_populates="exports")

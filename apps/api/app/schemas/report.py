from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReportCreateIn(BaseModel):
    molecule_a: str = Field(min_length=1, max_length=255)
    molecule_b: str = Field(min_length=1, max_length=255)
    topic: str = Field(min_length=1, max_length=512)
    options: dict = Field(default_factory=dict)
    # When true, bypass the cache and force a fresh evidence run.
    refresh: bool = False


class FreshnessOut(BaseModel):
    status: str  # up_to_date | update_available | unknown
    new_items: int = 0
    checked_at: datetime | None = None
    details: list[str] = []


class ClaimOut(BaseModel):
    text: str
    citation_ids: list[str] = []


class SectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    section_key: str
    title: str
    layer: str = "ai_interpretation"
    confidence: str
    insufficient_evidence: bool = False
    claims: list[ClaimOut] = []


class ComparisonRowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    attribute: str
    value_a: str
    value_b: str
    confidence: str
    rationale: str | None = None
    citation_ids: list[str] = []


class CitationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ref_key: str
    title: str
    source: str
    study_design: str | None = None
    doi: str | None = None
    pmid: str | None = None
    year: int | None = None
    verified: bool = False


class TrialExtractionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ref_key: str
    title: str
    study_design: str | None = None
    population: str | None = None
    intervention: str | None = None
    comparator: str | None = None
    sample_size: int | None = None
    outcomes: list[str] = []
    hazard_ratio: str | None = None
    relative_risk: str | None = None
    confidence_interval: str | None = None
    p_value: str | None = None
    adverse_events: list[str] = []
    strengths: list[str] = []
    limitations: list[str] = []
    extractor_model: str | None = None


class AgentRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    agent: str
    label: str
    state: str
    detail: str | None = None


class ReportSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    molecule_a: str
    molecule_b: str
    topic: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None


class MoleculeEvidenceSide(BaseModel):
    efficacy: int = 0
    safety: int = 0
    guideline: int = 0


class MoleculeEvidenceOut(BaseModel):
    a: MoleculeEvidenceSide
    b: MoleculeEvidenceSide


class ResearchProcessOut(BaseModel):
    """Transparency payload for the optional "Research Process" panel."""

    logs: list[dict] = Field(default_factory=list)  # per-agent execution log
    timings: dict = Field(default_factory=dict)  # agent_key -> ms
    snapshot: dict = Field(default_factory=dict)  # queries, counts, research plan
    verification: dict | None = None  # checked / verified / removed


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    molecule_a: str
    molecule_b: str
    topic: str
    model_synthesis: str | None = None
    cost_usd: float = 0
    freshness: str = "unknown"
    freshness_checked_at: datetime | None = None
    cached: bool = False
    conflicts: list[str] = Field(default_factory=list)
    sections: list[SectionOut] = []
    comparison: list[ComparisonRowOut] = Field(default_factory=list)
    citations: list[CitationOut] = []
    extractions: list[TrialExtractionOut] = Field(default_factory=list)
    agents: list[AgentRunOut] = Field(default_factory=list)
    molecule_evidence: MoleculeEvidenceOut | None = None
    # V3 multi-agent artifacts (present on V3 reports; null on legacy V2 reports).
    research_plan: dict | None = None
    scores: dict | None = None
    safety_matrix: dict | None = None
    reconciliation: dict | None = None
    visualizations: dict | None = None
    research_process: ResearchProcessOut | None = None

    @classmethod
    def from_report(cls, report, cached: bool = False) -> ReportOut:
        research_process = None
        if getattr(report, "agent_logs", None) or getattr(report, "source_snapshot", None):
            research_process = ResearchProcessOut(
                logs=report.agent_logs or [],
                timings=report.agent_timings or {},
                snapshot=report.source_snapshot or {},
                verification=getattr(report, "verification", None),
            )
        return cls(
            id=report.id,
            status=report.status,
            molecule_a=report.molecule_a,
            molecule_b=report.molecule_b,
            topic=report.topic,
            model_synthesis=report.model_synthesis,
            cost_usd=float(report.token_cost_usd or 0),
            freshness=report.freshness or "unknown",
            freshness_checked_at=report.freshness_checked_at,
            cached=cached,
            conflicts=report.conflicts or [],
            sections=[SectionOut.model_validate(s) for s in report.sections],
            comparison=[ComparisonRowOut.model_validate(r) for r in report.comparison_rows],
            citations=[CitationOut.model_validate(c) for c in report.citations],
            extractions=[TrialExtractionOut.model_validate(e) for e in report.extractions],
            agents=[AgentRunOut.model_validate(a) for a in report.agent_runs],
            molecule_evidence=(
                MoleculeEvidenceOut.model_validate(report.molecule_evidence)
                if report.molecule_evidence
                else None
            ),
            research_plan=getattr(report, "research_plan", None),
            scores=getattr(report, "evidence_scores", None),
            safety_matrix=getattr(report, "safety_matrix", None),
            reconciliation=getattr(report, "reconciliation", None),
            visualizations=getattr(report, "visualizations", None),
            research_process=research_process,
        )


class ShareOut(BaseModel):
    share_token: str
    url: str

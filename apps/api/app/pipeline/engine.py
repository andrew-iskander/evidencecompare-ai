"""RAG evidence engine — drives the multi-agent orchestrator and persists results.

The AI orchestrator (`app.agents.orchestrator`) runs the specialist agents over a
shared `PipelineState`; this module owns persistence: evidence docs + chunks
(embeddings), verified citations, structured trial extractions, comparison rows,
and report sections. Anti-hallucination guarantees are preserved end-to-end: only
verified citations are stored, and every rendered claim references a verified one.
"""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import PipelineState, _noop_progress
from app.agents.orchestrator import AIOrchestrator
from app.core.config import get_settings
from app.evidence.base import EvidenceSource
from app.models.report import (
    Citation,
    ComparisonRow,
    DocChunk,
    EvidenceDoc,
    Report,
    ReportSection,
    TrialExtraction,
)

log = logging.getLogger("pipeline.engine")


async def run_engine(
    db: AsyncSession,
    report: Report,
    on_progress=_noop_progress,
    sources: list[EvidenceSource] | None = None,
) -> dict:
    settings = get_settings()

    state = PipelineState(report.molecule_a, report.molecule_b, report.topic)
    state.sources = sources
    await AIOrchestrator().run(state, on_progress)

    # 1. Persist evidence docs + chunks (embeddings) for the ranked/selected set.
    evdoc_id_by_obj: dict[int, object] = {}
    for rd in state.ranked:
        ev = EvidenceDoc(
            source=rd.doc.source,
            external_id=rd.doc.external_id,
            doi=rd.doc.doi,
            pmid=rd.doc.pmid,
            title=rd.doc.title,
            study_design=rd.doc.study_design,
            publication_year=rd.doc.publication_year,
            sample_size=rd.doc.sample_size,
            doc_metadata=rd.doc.metadata,
        )
        db.add(ev)
        await db.flush()  # get ev.id
        evdoc_id_by_obj[id(rd)] = ev.id
        db.add(
            DocChunk(
                doc_id=ev.id,
                report_id=report.id,
                chunk_index=0,
                content=f"{rd.doc.title}. {rd.doc.abstract}"[:4000],
                embedding=rd.metadata.get("embedding", []),
            )
        )
    await db.commit()

    # 2. Citations — verified only, contiguous ref_keys c1..cN.
    for i, rd in enumerate(state.verified):
        db.add(
            Citation(
                report_id=report.id,
                doc_id=evdoc_id_by_obj.get(id(rd)),
                ref_key=rd.ref_key,
                title=rd.doc.title,
                source=rd.doc.source,
                study_design=rd.doc.study_design,
                doi=rd.doc.doi,
                pmid=rd.doc.pmid,
                year=rd.doc.publication_year,
                verified=True,
                order_index=i,
            )
        )
    await db.commit()

    # 3. Structured trial extractions, linked to their citation + evidence doc.
    ref_to_obj = {rd.ref_key: rd for rd in state.verified}
    for i, ex in enumerate(state.extractions):
        src_rd = ref_to_obj.get(ex["ref_key"])
        db.add(
            TrialExtraction(
                report_id=report.id,
                doc_id=evdoc_id_by_obj.get(id(src_rd)) if src_rd else None,
                ref_key=ex["ref_key"],
                title=ex["title"],
                study_design=ex["study_design"],
                population=ex["population"],
                intervention=ex["intervention"],
                comparator=ex["comparator"],
                sample_size=ex["sample_size"],
                outcomes=ex["outcomes"],
                hazard_ratio=ex["hazard_ratio"],
                relative_risk=ex["relative_risk"],
                confidence_interval=ex["confidence_interval"],
                p_value=ex["p_value"],
                adverse_events=ex["adverse_events"],
                strengths=ex["strengths"],
                limitations=ex["limitations"],
                extractor_model=ex["extractor_model"],
                order_index=i,
            )
        )
    await db.commit()

    # 4. Comparison rows + narrative sections.
    for i, row in enumerate(state.comparison):
        db.add(
            ComparisonRow(
                report_id=report.id,
                attribute=row["attribute"],
                value_a=row["value_a"],
                value_b=row["value_b"],
                confidence=row["confidence"],
                rationale=row.get("rationale"),
                citation_ids=row.get("citation_ids", []),
                order_index=i,
            )
        )
    for i, section in enumerate(state.sections):
        db.add(
            ReportSection(
                report_id=report.id,
                section_key=section["section_key"],
                title=section["title"],
                confidence=section["confidence"],
                insufficient_evidence=section.get("insufficient_evidence", False),
                claims=section["claims"],
                order_index=i,
            )
        )
    await db.commit()

    # 5. Provenance + living-evidence fingerprint.
    report.molecule_evidence = state.molecule_evidence
    report.model_synthesis = state.synthesis_model
    report.prompt_version = "orchestrator-v1"
    report.evidence_fingerprint = sorted({d.dedup_key() for d in state.raw_docs})
    report.freshness = "up_to_date"
    report.source_snapshot = {
        "evidence_mode": settings.evidence_mode,
        "llm_mode": settings.llm_mode,
        "candidates": len(state.raw_docs),
        "ranked": len(state.ranked),
        "verified": len(state.verified),
        "extractions": len(state.extractions),
        "queries": state.queries,
    }
    await db.commit()

    return {
        "candidates": len(state.raw_docs),
        "verified": len(state.verified),
        "cost_usd": state.cost_usd,
        "model_used": state.synthesis_model,
    }

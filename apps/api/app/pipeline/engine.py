"""Phase 3 RAG evidence engine.

retrieve (trusted sources) -> embed -> hybrid rank (GRADE) -> verify citations ->
synthesize (Claude live, or offline extractive). Persists evidence docs, chunks,
citations, comparison rows, and sections. Enforces: only verified citations are
persisted, and every rendered claim references a verified citation.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.evidence.base import EvidenceSource
from app.evidence.registry import retrieve_evidence
from app.llm.synthesizer import synthesize
from app.models.report import (
    Citation,
    ComparisonRow,
    DocChunk,
    EvidenceDoc,
    Report,
    ReportSection,
)
from app.pipeline.comparison import molecule_evidence
from app.rag.embeddings import cosine, embed_query, embed_texts
from app.rag.ranking import RankedDoc, rank_docs
from app.rag.verifier import verify_doc

log = logging.getLogger("pipeline.engine")

Progress = Callable[[str, str, str | None], Awaitable[None]]


async def _noop(agent: str, state: str, detail: str | None = None) -> None:  # pragma: no cover
    return None


async def run_engine(
    db: AsyncSession,
    report: Report,
    on_progress: Progress = _noop,
    sources: list[EvidenceSource] | None = None,
) -> dict:
    settings = get_settings()
    a, b, topic = report.molecule_a, report.molecule_b, report.topic

    # 1. Retrieve
    await on_progress("search", "running", None)
    docs = await retrieve_evidence(a, b, topic, sources=sources)
    await on_progress("search", "done", f"{len(docs)} candidate(s)")

    # 2. Quick evidence-type views (drive the specialist agents' progress)
    def count(*designs: str) -> int:
        return sum(1 for d in docs if d.study_design in designs)

    await on_progress("guideline", "done", f"{count('guideline')} guideline(s)")
    await on_progress("trial", "done", f"{count('rct', 'trial_registry')} trial(s)")
    await on_progress(
        "meta_analysis", "done", f"{count('meta_analysis', 'systematic_review')} review(s)"
    )
    await on_progress("safety", "done", f"{count('drug_label')} label(s)")

    # 3. Embed + rank
    await on_progress("ranking", "running", None)
    ranked: list[RankedDoc] = []
    if docs:
        texts = [f"{d.title}. {d.abstract}" for d in docs]
        doc_vecs = await embed_texts(texts)
        q_vec = await embed_query(f"{a} versus {b} for {topic}")
        relevances = [cosine(q_vec, dv) for dv in doc_vecs]
        ranked = rank_docs(docs, relevances)[: settings.top_k_citations]

        # Persist evidence docs + chunks (embeddings) for the selected set.
        vec_by_key = {d.dedup_key(): dv for d, dv in zip(docs, doc_vecs, strict=False)}
        for rd in ranked:
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
            rd.metadata["evidence_doc_id"] = ev.id
            db.add(
                DocChunk(
                    doc_id=ev.id,
                    report_id=report.id,
                    chunk_index=0,
                    content=f"{rd.doc.title}. {rd.doc.abstract}"[:4000],
                    embedding=vec_by_key.get(rd.doc.dedup_key(), []),
                )
            )
        await db.commit()
    await on_progress("ranking", "done", f"ranked {len(ranked)}")

    # 4. Verify citations
    await on_progress("verification", "running", None)
    verified: list[RankedDoc] = []
    for rd in ranked:
        ok = await verify_doc(rd.doc)
        if ok:
            verified.append(rd)
    # Re-key verified sequentially so ref_keys are contiguous (c1..cN).
    for i, rd in enumerate(verified):
        rd.ref_key = f"c{i + 1}"
    await on_progress("verification", "done", f"verified {len(verified)}/{len(ranked)}")

    for i, rd in enumerate(verified):
        db.add(
            Citation(
                report_id=report.id,
                doc_id=rd.metadata.get("evidence_doc_id"),
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

    # 5. Synthesize
    await on_progress("report", "running", None)
    result = await synthesize(a, b, topic, verified)

    for i, row in enumerate(result["comparison"]):
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
    for i, section in enumerate(result["sections"]):
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
    await on_progress("report", "done", result["model_used"])

    report.molecule_evidence = molecule_evidence(a, b, verified)
    report.model_synthesis = result["model_used"]
    report.prompt_version = "engine-v1"
    report.source_snapshot = {
        "evidence_mode": settings.evidence_mode,
        "llm_mode": settings.llm_mode,
        "candidates": len(docs),
        "ranked": len(ranked),
        "verified": len(verified),
    }
    await db.commit()

    return {
        "candidates": len(docs),
        "verified": len(verified),
        "cost_usd": result.get("cost_usd", 0.0),
        "model_used": result["model_used"],
    }

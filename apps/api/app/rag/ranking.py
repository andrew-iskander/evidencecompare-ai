from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.evidence.base import RawDoc

# Evidence hierarchy weight (evidence-pyramid inspired).
_DESIGN_WEIGHT = {
    "meta_analysis": 1.0,
    "systematic_review": 0.9,
    "guideline": 0.85,
    "rct": 0.8,
    "trial_registry": 0.5,
    "drug_label": 0.5,
    "other": 0.35,
}

@dataclass
class RankedDoc:
    doc: RawDoc
    relevance: float  # cosine similarity to the topic query
    design_score: float
    recency_score: float
    size_score: float
    score: float = 0.0
    ref_key: str = ""
    metadata: dict = field(default_factory=dict)


def _recency(year: int | None) -> float:
    if not year:
        return 0.4
    age = max(0, datetime.now(UTC).year - year)
    return max(0.1, 1.0 - age / 25.0)  # ~25y horizon


def _size(n: int | None) -> float:
    if not n:
        return 0.4
    # log-ish saturation
    if n >= 10000:
        return 1.0
    if n >= 1000:
        return 0.8
    if n >= 100:
        return 0.6
    return 0.45


def rank_docs(docs: list[RawDoc], relevances: list[float]) -> list[RankedDoc]:
    ranked: list[RankedDoc] = []
    for doc, rel in zip(docs, relevances, strict=False):
        design = _DESIGN_WEIGHT.get(doc.study_design or "other", 0.35)
        rec = _recency(doc.publication_year)
        size = _size(doc.sample_size)
        # Weighted composite: relevance and design dominate.
        score = 0.4 * rel + 0.3 * design + 0.15 * rec + 0.15 * size
        ranked.append(
            RankedDoc(
                doc=doc,
                relevance=rel,
                design_score=design,
                recency_score=rec,
                size_score=size,
                score=round(score, 4),
            )
        )
    ranked.sort(key=lambda r: r.score, reverse=True)
    for i, r in enumerate(ranked):
        r.ref_key = f"c{i + 1}"
    return ranked


def confidence_from(ranked: list[RankedDoc]) -> str:
    """GRADE-inspired section/row confidence from the supporting evidence set.

    Thin wrapper over `app.rag.grade.grade` (Phase 4) so every confidence label in
    the app is produced by the same scorer. Imported locally to avoid a cycle.
    """
    from app.rag.grade import grade

    return grade(ranked).level

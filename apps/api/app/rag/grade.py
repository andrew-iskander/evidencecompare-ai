"""GRADE-inspired confidence scoring for the medical comparison engine (Phase 4).

Turns a set of supporting evidence documents into a confidence *level* plus a
human-readable *rationale* built from explicit dimensions — study design,
evidence volume, consistency of tier, directness (topic relevance), recency, and
precision (sample size). The dimensions are already computed per document during
ranking (`RankedDoc.design_score` etc.), so this layer only aggregates and
explains them — no evidence is invented.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean

from app.rag.ranking import RankedDoc

# Composite dimension weights (sum ≈ 1.0). Design and volume dominate, matching
# how GRADE upgrades/downgrades certainty.
_WEIGHTS = {
    "design": 0.30,
    "volume": 0.20,
    "directness": 0.15,
    "consistency": 0.15,
    "recency": 0.10,
    "precision": 0.10,
}

_BANDS = [(0.72, "high"), (0.52, "moderate"), (0.34, "low")]

# Documents at or above this design weight are "high-tier" (RCT and above).
_HIGH_TIER = 0.8
# Number of supporting documents at which the volume dimension saturates.
_VOLUME_SATURATION = 4


@dataclass
class GradeResult:
    level: str  # high | moderate | low | very_low
    score: float
    rationale: str
    dimensions: dict[str, float] = field(default_factory=dict)


def _band(score: float) -> str:
    for threshold, label in _BANDS:
        if score >= threshold:
            return label
    return "very_low"


def grade(docs: list[RankedDoc]) -> GradeResult:
    """Aggregate supporting evidence into a GRADE-style confidence result."""
    if not docs:
        return GradeResult(
            level="very_low",
            score=0.0,
            rationale="No supporting evidence was retrieved.",
            dimensions={},
        )

    n = len(docs)
    high_tier = [d for d in docs if d.design_score >= _HIGH_TIER]

    dims = {
        "design": max(d.design_score for d in docs),
        "volume": min(1.0, n / _VOLUME_SATURATION),
        # directness ≈ how on-topic the supporting docs are (cosine to the query).
        "directness": max(0.0, min(1.0, mean(d.relevance for d in docs))),
        # consistency ≈ share of docs at the high-evidence tier (tier agreement).
        "consistency": (len(high_tier) / n) if n else 0.0,
        "recency": mean(d.recency_score for d in docs),
        "precision": mean(d.size_score for d in docs),
    }

    score = sum(_WEIGHTS[k] * v for k, v in dims.items())
    # Certainty cannot be high without at least one high-tier study.
    if not high_tier:
        score = min(score, 0.55)
    score = round(score, 4)
    level = _band(score)

    dims = {k: round(v, 3) for k, v in dims.items()}
    return GradeResult(
        level=level, score=score, rationale=_rationale(docs, dims, level), dimensions=dims
    )


_DESIGN_LABEL = {
    "meta_analysis": "meta-analysis",
    "systematic_review": "systematic review",
    "guideline": "guideline",
    "rct": "randomized trial",
    "trial_registry": "registered trial",
    "drug_label": "drug label",
    "other": "other source",
}


def _rationale(docs: list[RankedDoc], dims: dict[str, float], level: str) -> str:
    n = len(docs)
    designs = sorted({d.doc.study_design or "other" for d in docs})
    tiers = ", ".join(_DESIGN_LABEL.get(d, d) for d in designs)
    parts = [
        f"{level.replace('_', ' ').title()} certainty from {n} supporting item(s) ({tiers})."
    ]
    if dims["consistency"] < 0.5:
        parts.append(
            "Evidence rests largely on lower-tier designs (directness/consistency limited)."
        )
    if dims["volume"] < 0.5:
        parts.append("Sparse volume of directly supporting evidence.")
    if dims["precision"] < 0.5:
        parts.append("Sample sizes are small or unreported (imprecision).")
    return " ".join(parts)

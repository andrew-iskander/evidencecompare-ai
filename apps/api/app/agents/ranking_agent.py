"""Evidence-Ranking Agent — scores the selected evidence base.

In V3 study *selection* and relevance ranking happen in the Search Agent; this
agent produces the interpretable *quality scores* the report and visualizations
consume. It is fully deterministic (no LLM, no network): every score is a function
of the retrieved study designs, sizes, recency, topical relevance (already computed
during ranking) and the extracted effect directions — so it never invents evidence,
only characterizes what was retrieved.

Per the V3 spec it emits, per study and overall:
  evidence score · quality score · risk of bias · confidence · publication quality
  · consistency score

plus each study's position in the evidence hierarchy (Guidelines → Meta-analysis →
Systematic Review → RCT → Cohort → Registry → Observational → Mechanistic → Animal).
"""

from __future__ import annotations

from typing import Any

from app.agents.base import Agent, AgentOutcome, PipelineState
from app.pipeline.quality import _direction  # reuse effect-direction parser
from app.rag.grade import grade
from app.rag.ranking import RankedDoc

# V3 evidence hierarchy → rank (1 = strongest). Keyword hints let us separate
# cohort/observational/mechanistic/animal, which share the "other" design bucket.
_TIER_RANK = {
    "guideline": 1,
    "meta_analysis": 2,
    "systematic_review": 3,
    "rct": 4,
    "trial_registry": 6,
    "drug_label": 6,
    "other": 7,
}

_TIER_LABEL = {
    1: "Guideline",
    2: "Meta-analysis",
    3: "Systematic Review",
    4: "Randomized Trial",
    5: "Cohort",
    6: "Registry",
    7: "Observational",
    8: "Mechanistic",
    9: "Animal",
}


def _tier(rd: RankedDoc) -> int:
    design = rd.doc.study_design or "other"
    base = _TIER_RANK.get(design, 7)
    if base >= 7:  # refine the "other" bucket from free text
        hay = f"{rd.doc.title} {rd.doc.abstract}".lower()
        if any(k in hay for k in ("animal", "murine", "rat model", "mouse", "in vivo model")):
            return 9
        if any(k in hay for k in ("in vitro", "mechanism", "receptor binding", "pharmacodynam")):
            return 8
        if any(k in hay for k in ("cohort", "prospective observational")):
            return 5
    return base


def _risk_of_bias(rd: RankedDoc) -> str:
    """Coarse risk-of-bias band from design + reporting cues (never a clinical claim)."""
    design = rd.doc.study_design or "other"
    hay = f"{rd.doc.title} {rd.doc.abstract}".lower()
    if rd.doc.metadata.get("synthetic"):
        return "unassessed"
    if design in ("meta_analysis", "systematic_review"):
        return "low" if "randomized" in hay else "moderate"
    if design == "rct":
        blinded = "double-blind" in hay or "double blind" in hay
        large = (rd.doc.sample_size or 0) >= 1000
        return "low" if (blinded and large) else "moderate"
    if design == "guideline":
        return "low"
    return "high"


def _publication_quality(rd: RankedDoc) -> float:
    """0..1 proxy for publication quality: identifiers + recency + evidence tier."""
    q = 0.0
    if rd.doc.doi or rd.doc.pmid:
        q += 0.4  # indexed/resolvable record
    q += 0.3 * rd.design_score
    q += 0.3 * rd.recency_score
    return round(min(1.0, q), 3)


def _pct(x: float) -> int:
    return int(round(max(0.0, min(1.0, x)) * 100))


def _consistency(ranked: list[RankedDoc], extractions: list[dict]) -> float:
    """Agreement of significant primary effect directions across studies (0..1)."""
    dirs = [
        d[0]
        for ex in extractions
        if (d := _direction(ex)) and d[1] and d[0] in ("favors", "against")
    ]
    if len(dirs) < 2:
        return 1.0  # nothing to disagree
    majority = max(dirs.count("favors"), dirs.count("against"))
    return round(majority / len(dirs), 3)


class EvidenceRankingAgent(Agent):
    key = "ranking"
    label = "Evidence-Ranking Agent"
    model = "claude-haiku-4-5"

    async def run(self, state: PipelineState) -> AgentOutcome:
        ranked = state.ranked
        if not ranked:
            state.scores = {"overall": {}, "studies": []}
            return AgentOutcome(detail="no evidence to score")

        g = grade(ranked)
        consistency = _consistency(ranked, state.extractions)

        studies: list[dict[str, Any]] = []
        for rd in ranked:
            tier = _tier(rd)
            quality = round((rd.design_score + rd.recency_score + rd.size_score) / 3, 3)
            studies.append(
                {
                    "ref_key": rd.ref_key,
                    "title": rd.doc.title,
                    "study_design": rd.doc.study_design,
                    "tier_rank": tier,
                    "tier_label": _TIER_LABEL.get(tier, "Other"),
                    "evidence_score": _pct(rd.score),
                    "quality_score": _pct(quality),
                    "risk_of_bias": _risk_of_bias(rd),
                    "publication_quality": _pct(_publication_quality(rd)),
                    "relevance": round(rd.relevance, 3),
                }
            )
        studies.sort(key=lambda s: (s["tier_rank"], -s["evidence_score"]))

        overall = {
            "evidence_score": _pct(g.score),
            "quality_score": _pct(g.dimensions.get("precision", 0.4) * 0.5
                                  + g.dimensions.get("design", 0.0) * 0.5),
            "confidence": g.level,
            "consistency_score": _pct(consistency),
            "publication_quality": _pct(
                sum(s["publication_quality"] for s in studies) / len(studies) / 100
            ),
            "risk_of_bias": (
                "low"
                if sum(1 for s in studies if s["risk_of_bias"] == "low") >= len(studies) / 2
                else "moderate"
            ),
            "dimensions": g.dimensions,
            "rationale": g.rationale,
            "n_studies": len(studies),
        }
        state.scores = {"overall": overall, "studies": studies}
        state.snapshot["scores"] = overall

        return AgentOutcome(
            detail=(
                f"scored {len(studies)} studies; evidence {overall['evidence_score']}/100, "
                f"consistency {overall['consistency_score']}/100, confidence {g.level}"
            )
        )

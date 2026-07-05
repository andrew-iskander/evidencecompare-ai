"""Visualization Agent — precomputes payloads for the interactive report charts.

Turns the verified evidence, structured extractions, scores, guideline summary and
safety matrix into ready-to-render data for the frontend visualizations: evidence
timeline, evidence pyramid, guideline comparison matrix, risk–benefit matrix,
safety heatmap, confidence meter, forest-plot summary, and a study/molecule network
graph. It computes nothing new about the drugs — it only reshapes evidence that
earlier agents already verified, so charts and prose stay in lockstep.
"""

from __future__ import annotations

import re
from typing import Any

from app.agents.base import Agent, AgentOutcome, PipelineState
from app.agents.specialists import mentions
from app.pipeline.comparison import molecule_evidence
from app.pipeline.quality import _ci_bounds
from app.rag.ranking import RankedDoc

_TIER_ORDER = [
    "meta_analysis", "systematic_review", "guideline", "rct", "trial_registry",
    "drug_label", "other",
]
_TIER_LABEL = {
    "meta_analysis": "Meta-analysis", "systematic_review": "Systematic Review",
    "guideline": "Guideline", "rct": "Randomized Trial", "trial_registry": "Registry",
    "drug_label": "Drug Label", "other": "Other",
}
_NUM = re.compile(r"([0-9]+(?:\.[0-9]+)?)")


def _timeline(verified: list[RankedDoc]) -> list[dict]:
    items = [
        {"ref_key": rd.ref_key, "year": rd.doc.publication_year,
         "title": rd.doc.title, "design": rd.doc.study_design, "source": rd.doc.source}
        for rd in verified if rd.doc.publication_year
    ]
    return sorted(items, key=lambda x: x["year"])


def _pyramid(verified: list[RankedDoc]) -> list[dict]:
    counts: dict[str, int] = {}
    for rd in verified:
        counts[rd.doc.study_design or "other"] = counts.get(rd.doc.study_design or "other", 0) + 1
    return [
        {"tier": d, "label": _TIER_LABEL[d], "count": counts[d]}
        for d in _TIER_ORDER if counts.get(d)
    ]


def _forest(extractions: list[dict]) -> list[dict]:
    out = []
    for ex in extractions:
        text = ex.get("hazard_ratio") or ex.get("relative_risk")
        if not text:
            continue
        m = _NUM.search(text)
        if not m:
            continue
        point = float(m.group(1))
        ci = _ci_bounds(ex.get("confidence_interval"))
        out.append({
            "ref_key": ex["ref_key"],
            "label": ex["title"][:60],
            "measure": "HR" if ex.get("hazard_ratio") else "RR",
            "point": point,
            "low": ci[0] if ci else None,
            "high": ci[1] if ci else None,
        })
    return out


def _network(verified: list[RankedDoc], a: str, b: str) -> dict:
    nodes: list[dict[str, Any]] = [
        {"id": f"mol:{a}", "type": "molecule", "label": a},
        {"id": f"mol:{b}", "type": "molecule", "label": b},
    ]
    edges: list[dict[str, Any]] = []
    for rd in verified:
        nodes.append({"id": rd.ref_key, "type": "study", "label": rd.doc.title[:50],
                      "design": rd.doc.study_design})
        if mentions(rd, a):
            edges.append({"source": rd.ref_key, "target": f"mol:{a}"})
        if mentions(rd, b):
            edges.append({"source": rd.ref_key, "target": f"mol:{b}"})
    return {"nodes": nodes, "edges": edges}


def _safety_heatmap(matrix: dict | None) -> list[dict]:
    if not matrix:
        return []
    return [
        {"domain": row["label"],
         "a": row["a"]["status"] == "reported",
         "b": row["b"]["status"] == "reported"}
        for row in matrix.get("rows", [])
    ]


def _guideline_matrix(summary: dict | None) -> list[dict]:
    if not summary:
        return []
    return [
        {"text": c["text"], "citation_ids": c.get("citation_ids", [])}
        for c in summary.get("claims", [])
    ]


class VisualizationAgent(Agent):
    key = "visualization"
    label = "Visualization Agent"
    model = "claude-haiku-4-5"

    async def run(self, state: PipelineState) -> AgentOutcome:
        a, b = state.molecule_a, state.molecule_b
        verified = state.verified
        overall = state.scores.get("overall", {})

        state.visualizations = {
            "timeline": _timeline(verified),
            "pyramid": _pyramid(verified),
            "guideline_matrix": _guideline_matrix(state.guideline_summary),
            "risk_benefit": molecule_evidence(a, b, verified),
            "safety_heatmap": _safety_heatmap(state.safety_matrix),
            "confidence_meter": {
                "confidence": overall.get("confidence", "very_low"),
                "evidence_score": overall.get("evidence_score", 0),
                "consistency_score": overall.get("consistency_score", 0),
            },
            "forest": _forest(state.extractions),
            "network": _network(verified, a, b),
        }
        built = sum(1 for v in state.visualizations.values() if v)
        return AgentOutcome(detail=f"{built} visualization payload(s) built")

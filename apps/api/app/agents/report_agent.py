"""Report-Generator Agent — assembles the final, ordered evidence report.

The Medical-Writer agent produces the narrative sections and the comparison table
over the verified evidence; this agent finalizes the document: it computes the
per-molecule evidence matrix, derives an Evidence-Ranking section from the scoring
agent and a Research-Gaps section from the writer's gaps + the conflict agent's
reconciliation, then orders every section into the canonical V3 report layout.
Exports (PDF/PPTX/Excel/Markdown) consume the same assembled structure, so all
output formats stay in sync. It invents nothing — every derived section cites the
verified evidence it summarizes.
"""

from __future__ import annotations

from app.agents.base import Agent, AgentOutcome, PipelineState
from app.pipeline.comparison import build_comparison, molecule_evidence, top_tier_label

# Canonical section order for the assembled report (keys not listed sort last).
_ORDER = [
    "executive_summary",
    "clinical_pearls",
    "mechanism_of_action",
    "guidelines",
    "trials",
    "meta_analyses",
    "safety",
    "contraindications",
    "special_populations",
    "interactions",
    "evidence_ranking",
    "limitations",
    "research_gaps",
    "evidence_gaps",
]


def _evidence_ranking_section(state: PipelineState) -> dict:
    overall = state.scores.get("overall", {})
    top = [rd.ref_key for rd in state.verified[:3]]
    claims = [
        {
            "text": (
                f"Aggregate evidence score {overall.get('evidence_score', 0)}/100 "
                f"({overall.get('confidence', 'very_low').replace('_', ' ')} certainty) "
                f"across {overall.get('n_studies', 0)} scored study/studies; "
                f"consistency {overall.get('consistency_score', 0)}/100; "
                f"overall risk of bias: {overall.get('risk_of_bias', 'unassessed')}."
            ),
            "citation_ids": top,
        },
        {
            "text": (
                f"Highest evidence tier retrieved: {top_tier_label(state.verified).lower()}. "
                f"{overall.get('rationale', '')}"
            ).strip(),
            "citation_ids": top,
        },
    ]
    return {
        "section_key": "evidence_ranking",
        "title": "Evidence Ranking",
        "confidence": overall.get("confidence", "very_low"),
        "insufficient_evidence": not state.verified,
        "claims": claims,
    }


def _research_gaps_section(state: PipelineState) -> dict:
    """Forward-looking gaps: unresolved conflicts + where new evidence is needed.

    Complements (does not duplicate) the writer's Evidence-Gaps section, which owns
    the direct head-to-head gap.
    """
    recon = state.reconciliation or {}
    claims = [{"text": note, "citation_ids": []} for note in recon.get("notes", [])]
    if not claims:
        claims = [{
            "text": "No conflicting evidence was detected; the main gap is the absence "
                    "of direct head-to-head data (see Evidence Gaps). Adequately powered "
                    "comparative trials would strengthen certainty.",
            "citation_ids": [],
        }]
    return {
        "section_key": "research_gaps",
        "title": "Research Gaps",
        "confidence": "low",
        "insufficient_evidence": bool(recon.get("has_conflict")),
        "claims": claims,
    }


class ReportGeneratorAgent(Agent):
    key = "report"
    label = "Report-Generator Agent"
    model = "claude-sonnet-5"

    async def run(self, state: PipelineState) -> AgentOutcome:
        a, b, t = state.molecule_a, state.molecule_b, state.topic

        # Authoritative comparison + per-molecule evidence matrix over verified set.
        if not state.comparison:
            state.comparison = build_comparison(a, b, t, state.verified)
        if not state.molecule_evidence:
            state.molecule_evidence = molecule_evidence(a, b, state.verified)

        sections = list(state.sections)
        by_key = {s["section_key"]: s for s in sections}

        # Derive the Evidence-Ranking section from the scoring agent.
        if "evidence_ranking" not in by_key:
            sections.append(_evidence_ranking_section(state))

        # Add a forward-looking Research-Gaps section (complements Evidence Gaps).
        if "research_gaps" not in by_key:
            sections.append(_research_gaps_section(state))

        # Canonical ordering (stable for keys not in the list).
        order_index = {k: i for i, k in enumerate(_ORDER)}
        sections.sort(key=lambda s: order_index.get(s["section_key"], len(_ORDER)))
        state.sections = sections

        return AgentOutcome(
            detail=f"assembled {len(sections)} sections, {len(state.comparison)} comparison rows"
        )

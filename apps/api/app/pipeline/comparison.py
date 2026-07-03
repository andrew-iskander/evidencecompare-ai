"""Medical comparison engine (Phase 4).

Builds the comprehensive side-by-side comparison table from the classified,
verified evidence. Every row carries A vs B values, a GRADE confidence level, the
supporting verified citations, and a plain-language rationale for the score. Rows
characterize the *evidence base* per molecule — they never assert a clinical
outcome that the retrieved evidence does not support.
"""

from __future__ import annotations

from app.agents.specialists import DomainResult, analyze, head_to_head, mentions
from app.rag.grade import grade
from app.rag.ranking import RankedDoc

# Evidence-tier display order (best first).
_TIER_ORDER = [
    "meta_analysis", "systematic_review", "guideline", "rct", "trial_registry", "drug_label",
]
_TIER_LABEL = {
    "meta_analysis": "Meta-analysis",
    "systematic_review": "Systematic review",
    "guideline": "Guideline",
    "rct": "RCT",
    "trial_registry": "Registered trial",
    "drug_label": "Drug label",
}


def top_tier_label(docs: list[RankedDoc]) -> str:
    present = {d.doc.study_design for d in docs}
    for tier in _TIER_ORDER:
        if tier in present:
            return _TIER_LABEL[tier]
    return "None retrieved"


def _cite(docs: list[RankedDoc], limit: int = 3) -> list[str]:
    return [d.ref_key for d in docs[:limit]]


def _row(
    attribute: str,
    value_a: str,
    value_b: str,
    supporting: list[RankedDoc],
) -> dict:
    g = grade(supporting)
    return {
        "attribute": attribute,
        "value_a": value_a,
        "value_b": value_b,
        "confidence": g.level,
        "citation_ids": _cite(supporting),
        "rationale": g.rationale,
    }


def _volume_value(docs: list[RankedDoc]) -> str:
    if not docs:
        return "No evidence retrieved"
    return f"{len(docs)} item(s); highest tier: {top_tier_label(docs)}"


def _domain_row(attribute: str, dr: DomainResult) -> dict:
    """A comparison row for one clinical domain, attributed per molecule."""
    return _row(
        attribute,
        _volume_value(dr.a_docs),
        _volume_value(dr.b_docs),
        dr.docs,
    )


# Macro-domains for the per-molecule risk-benefit positioning.
_EFFICACY_DOMAINS = ("trials", "meta_analyses")
_SAFETY_DOMAINS = ("safety", "contraindications", "interactions", "special_populations")
_GUIDELINE_DOMAINS = ("guidelines",)


def molecule_evidence(
    molecule_a: str, molecule_b: str, verified: list[RankedDoc]
) -> dict:
    """Per-molecule evidence counts by macro-domain (drives the risk-benefit matrix).

    Counts distinct citations (by ref_key) attributed to each molecule so a
    document spanning several safety sub-domains is not double-counted.
    """
    domains = analyze(molecule_a, molecule_b, verified)

    def count(keys: tuple[str, ...], side: str) -> int:
        refs: set[str] = set()
        for k in keys:
            for rd in getattr(domains[k], side):
                refs.add(rd.ref_key)
        return len(refs)

    def side(attr: str) -> dict:
        return {
            "efficacy": count(_EFFICACY_DOMAINS, attr),
            "safety": count(_SAFETY_DOMAINS, attr),
            "guideline": count(_GUIDELINE_DOMAINS, attr),
        }

    return {"a": side("a_docs"), "b": side("b_docs")}


def build_comparison(
    molecule_a: str, molecule_b: str, topic: str, verified: list[RankedDoc]
) -> list[dict]:
    """Comprehensive comparison rows with GRADE confidence + rationale."""
    a, b = molecule_a, molecule_b
    domains = analyze(a, b, verified)
    a_docs = [d for d in verified if mentions(d, a)]
    b_docs = [d for d in verified if mentions(d, b)]
    h2h = head_to_head(verified, a, b)

    rows: list[dict] = [
        _row(
            "Overall evidence base",
            _volume_value(a_docs),
            _volume_value(b_docs),
            verified,
        ),
        _domain_row("Randomized-trial evidence", domains["trials"]),
        _domain_row("Meta-analytic / systematic-review evidence", domains["meta_analyses"]),
        _domain_row("Guideline recommendation coverage", domains["guidelines"]),
        _domain_row("Safety / labeling evidence", domains["safety"]),
        _domain_row("Special-population evidence", domains["special_populations"]),
    ]

    # Direct head-to-head: only trials comparing A vs B qualify.
    h2h_grade = grade(h2h)
    rows.append(
        {
            "attribute": "Direct head-to-head comparison",
            "value_a": "Identified" if h2h else "Insufficient direct evidence",
            "value_b": "Identified" if h2h else "Insufficient direct evidence",
            "confidence": h2h_grade.level if h2h else "very_low",
            "citation_ids": _cite(h2h),
            "rationale": (
                h2h_grade.rationale
                if h2h
                else f"No retrieved trial directly compares {a} and {b} on {topic}."
            ),
        }
    )
    return rows

"""Medical comparison-engine tests (Phase 4)."""

from __future__ import annotations

import asyncio

from app.agents.specialists import analyze, head_to_head
from app.evidence.base import RawDoc
from app.evidence.offline_fixtures import OfflineSource
from app.pipeline.comparison import build_comparison, molecule_evidence
from app.rag.ranking import rank_docs

A, B, TOPIC = "Telmisartan", "Valsartan", "Cardioprotection"


def _verified():
    docs = asyncio.run(OfflineSource().search(A, B, TOPIC, 12))
    ranked = rank_docs(docs, [0.5] * len(docs))
    for i, rd in enumerate(ranked):
        rd.ref_key = f"c{i + 1}"
    return ranked


def test_rows_are_complete_and_grounded():
    verified = _verified()
    valid = {rd.ref_key for rd in verified}
    rows = build_comparison(A, B, TOPIC, verified)
    assert len(rows) >= 6
    required = {"attribute", "value_a", "value_b", "confidence", "citation_ids", "rationale"}
    for row in rows:
        assert required <= row.keys()
        assert row["confidence"] in ("high", "moderate", "low", "very_low")
        assert row["rationale"]
        assert set(row["citation_ids"]) <= valid  # only verified refs are cited


def test_head_to_head_row_is_insufficient_offline():
    # Offline fixtures have only single-molecule trials → no direct A-vs-B trial.
    rows = build_comparison(A, B, TOPIC, _verified())
    h2h = next(r for r in rows if r["attribute"] == "Direct head-to-head comparison")
    assert h2h["confidence"] == "very_low"
    assert h2h["citation_ids"] == []
    assert "Insufficient" in h2h["value_a"]


def test_head_to_head_detects_a_real_comparative_trial():
    verified = _verified()
    trial = RawDoc(
        source="pubmed",
        title=f"Head-to-head RCT of {A} versus {B} for {TOPIC}",
        pmid="99999999",
        study_design="rct",
        metadata={"molecules": [A, B]},
    )
    combined = rank_docs(
        [rd.doc for rd in verified] + [trial], [0.5] * (len(verified) + 1)
    )
    for i, rd in enumerate(combined):
        rd.ref_key = f"c{i + 1}"
    assert head_to_head(combined, A, B)


def test_molecule_evidence_counts_per_molecule():
    me = molecule_evidence(A, B, _verified())
    assert set(me) == {"a", "b"}
    for side in me.values():
        assert set(side) == {"efficacy", "safety", "guideline"}
        assert all(isinstance(v, int) and v >= 0 for v in side.values())
    # Each molecule has its own single-molecule RCT → efficacy evidence for both.
    assert me["a"]["efficacy"] >= 1
    assert me["b"]["efficacy"] >= 1


def test_domain_attribution_splits_by_molecule():
    domains = analyze(A, B, _verified())
    trials = domains["trials"]
    # The two offline single-molecule RCTs attribute to A and B respectively.
    assert any(A.lower() in f"{rd.doc.title} {rd.doc.abstract}".lower() for rd in trials.a_docs)
    assert any(B.lower() in f"{rd.doc.title} {rd.doc.abstract}".lower() for rd in trials.b_docs)

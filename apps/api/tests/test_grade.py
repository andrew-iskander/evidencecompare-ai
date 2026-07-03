"""GRADE confidence-scorer tests (Phase 4)."""

from __future__ import annotations

from app.evidence.base import RawDoc
from app.rag.grade import grade
from app.rag.ranking import rank_docs


def _ranked(*docs: RawDoc):
    return rank_docs(list(docs), [0.7] * len(docs))


def test_empty_evidence_is_very_low():
    result = grade([])
    assert result.level == "very_low"
    assert result.score == 0.0
    assert "No supporting evidence" in result.rationale


def test_high_tier_beats_low_tier():
    meta = RawDoc(source="europepmc", title="m", study_design="meta_analysis",
                  pmid="1", publication_year=2023, sample_size=20000)
    label = RawDoc(source="fda", title="l", study_design="drug_label", external_id="x")
    strong = grade(_ranked(meta))
    weak = grade(_ranked(label))
    assert strong.score > weak.score
    assert weak.level in ("low", "very_low")


def test_no_high_tier_cannot_be_high():
    label = RawDoc(source="fda", title="l", study_design="drug_label", external_id="x",
                   publication_year=2024, sample_size=99999)
    # Even with maxed recency/precision, a lone low-tier source is not "high".
    assert grade(_ranked(label)).level != "high"


def test_rationale_reports_count_and_tiers():
    rct = RawDoc(source="pubmed", title="r", study_design="rct", pmid="2",
                 publication_year=2022, sample_size=3000)
    result = grade(_ranked(rct))
    assert "1 supporting item" in result.rationale
    assert "randomized trial" in result.rationale
    assert set(result.dimensions) == {
        "design", "volume", "directness", "consistency", "recency", "precision"
    }

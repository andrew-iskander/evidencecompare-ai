"""U3 tests: transparency layers, conflicting-evidence detection, clinical pearls."""

from __future__ import annotations

import asyncio

from app.evidence.offline_fixtures import OfflineSource
from app.llm.synthesizer import offline_synthesize
from app.pipeline.quality import detect_conflicts, layer_for
from app.rag.ranking import rank_docs

A, B, TOPIC = "Telmisartan", "Valsartan", "Cardioprotection"


def test_layer_assignment():
    assert layer_for("executive_summary") == "clinical_summary"
    assert layer_for("clinical_pearls") == "clinical_summary"
    assert layer_for("trials") == "ai_interpretation"
    assert layer_for("safety") == "ai_interpretation"


def test_no_conflict_when_directions_agree():
    # One significant benefit + one non-significant trend → no conflict.
    ex = [
        {"intervention": "Foo", "title": "t", "hazard_ratio": "HR 0.80",
         "confidence_interval": "95% CI 0.70-0.92", "p_value": "p=0.01"},
        {"intervention": "Foo", "title": "t", "relative_risk": "RR 0.95",
         "confidence_interval": "95% CI 0.85-1.06", "p_value": "p=0.30"},
    ]
    assert detect_conflicts(ex, "Foo", "Bar") == []


def test_conflict_detected_on_opposite_significant_directions():
    ex = [
        {"intervention": "Foo", "title": "study 1", "hazard_ratio": "HR 0.70",
         "confidence_interval": "95% CI 0.55-0.89", "p_value": "p=0.004"},
        {"intervention": "Foo", "title": "study 2", "hazard_ratio": "HR 1.45",
         "confidence_interval": "95% CI 1.12-1.88", "p_value": "p=0.01"},
    ]
    notes = detect_conflicts(ex, "Foo", "Bar")
    assert len(notes) == 1
    assert "Foo" in notes[0]


def test_offline_synthesis_includes_clinical_pearls():
    docs = asyncio.run(OfflineSource().search(A, B, TOPIC, 12))
    ranked = rank_docs(docs, [0.5] * len(docs))
    for i, rd in enumerate(ranked):
        rd.ref_key = f"c{i + 1}"
    result = offline_synthesize(A, B, TOPIC, ranked)
    keys = {s["section_key"] for s in result["sections"]}
    assert "clinical_pearls" in keys
    pearls = next(s for s in result["sections"] if s["section_key"] == "clinical_pearls")
    assert pearls["claims"], "clinical pearls should have content when evidence exists"

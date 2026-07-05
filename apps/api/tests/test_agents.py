"""Multi-agent orchestrator tests (offline, deterministic).

Runs the full V3 agent chain over the offline fixtures with no network or API keys
and locks: all twelve agents run in the spec order, the specialist artifacts are
produced (research plan, scores, safety matrix, reconciliation, verification report,
visualizations), and the anti-hallucination contract holds end-to-end (every
rendered citation is a verified ref; head-to-head absence is reported honestly).
"""

from __future__ import annotations

import asyncio

from app.agents.base import PipelineState
from app.agents.orchestrator import DEFAULT_AGENTS, DEFAULT_PLAN, AIOrchestrator
from app.evidence.offline_fixtures import OfflineSource

A, B, TOPIC = "Telmisartan", "Valsartan", "Cardioprotection"

_EXPECTED_ORDER = [
    "interpreter", "search", "guideline", "extraction", "ranking", "safety",
    "conflict", "verification", "writer", "visualization", "report", "monitor",
]


def _run(coro):
    return asyncio.run(coro)


def _state() -> PipelineState:
    state = PipelineState(A, B, TOPIC)
    state.sources = [OfflineSource()]

    async def go() -> PipelineState:
        await AIOrchestrator().run(state)
        return state

    return _run(go())


def test_all_twelve_agents_run_in_order():
    keys = [a.key for a in DEFAULT_AGENTS]
    assert keys == _EXPECTED_ORDER
    # Every agent belongs to exactly one stage; the plan flattens to the roster.
    assert [a.key for stage in DEFAULT_PLAN for a in stage] == keys


def test_orchestrator_produces_full_report():
    state = _state()
    assert state.raw_docs, "search agent retrieved candidates"
    assert state.ranked, "search agent produced a ranked study list"
    assert state.verified, "citation-verification produced verified citations"
    assert state.sections, "writer produced sections"
    assert state.comparison, "report generator produced comparison rows"
    assert state.queries, "search agent recorded optimized queries"
    assert state.research_plan and state.research_plan["pico"], "interpreter built PICO"
    assert state.molecule_evidence, "report generator built the molecule matrix"


def test_interpreter_expands_search_terms():
    state = _state()
    plan = state.research_plan
    assert plan["pico"]["intervention"] == A
    assert plan["pico"]["comparator"] == B
    # Telmisartan/Valsartan carry offline synonyms that widen the keyword set.
    assert len(plan["expanded_keywords"]) > 3


def test_evidence_ranking_scores():
    state = _state()
    overall = state.scores["overall"]
    for k in ("evidence_score", "quality_score", "consistency_score", "confidence",
              "risk_of_bias", "publication_quality"):
        assert k in overall
    assert 0 <= overall["evidence_score"] <= 100
    assert state.scores["studies"], "per-study scores present"
    assert all(1 <= s["tier_rank"] <= 9 for s in state.scores["studies"])


def test_safety_matrix_is_comparative_and_cited():
    state = _state()
    matrix = state.safety_matrix
    assert matrix and matrix["rows"]
    domain_keys = {r["key"] for r in matrix["rows"]}
    for expected in ("contraindications", "interactions", "pregnancy", "renal",
                     "hepatic", "adverse_events"):
        assert expected in domain_keys
    valid = {rd.ref_key for rd in state.verified}
    for row in matrix["rows"]:
        for side in ("a", "b"):
            assert set(row[side]["citation_ids"]) <= valid


def test_conflict_agent_reports_reconciliation():
    state = _state()
    recon = state.reconciliation
    assert recon is not None
    assert "has_conflict" in recon and "summary" in recon
    assert isinstance(state.conflicts, list)


def test_verification_report_and_stable_keys():
    state = _state()
    v = state.verification
    assert v["checked"] >= v["verified"] >= 1
    # Offline: all trusted records resolve, so keys are contiguous c1..cN.
    keys = [rd.ref_key for rd in state.verified]
    assert keys == [f"c{i + 1}" for i in range(len(keys))]


def test_visualizations_built():
    state = _state()
    viz = state.visualizations
    for key in ("timeline", "pyramid", "risk_benefit", "safety_heatmap",
                "confidence_meter", "network"):
        assert key in viz
    # Network graph references only verified studies + the two molecule nodes.
    node_ids = {n["id"] for n in viz["network"]["nodes"]}
    assert f"mol:{A}" in node_ids and f"mol:{B}" in node_ids


def test_execution_logs_and_timings():
    state = _state()
    assert len(state.logs) == 12, "one execution-log entry per agent"
    assert set(state.timings) == set(_EXPECTED_ORDER)
    assert all(entry["state"] in ("done", "error") for entry in state.logs)


def test_extraction_parses_effect_sizes():
    state = _state()
    assert state.extractions, "trial-extraction agent produced records"
    hrs = [e["hazard_ratio"] for e in state.extractions if e["hazard_ratio"]]
    rrs = [e["relative_risk"] for e in state.extractions if e["relative_risk"]]
    assert any("0.86" in h for h in hrs), f"expected parsed HR, got {hrs}"
    assert any("0.91" in r for r in rrs), f"expected parsed RR, got {rrs}"
    assert any(e["adverse_events"] for e in state.extractions)


def test_orchestrator_citations_are_verified_only():
    state = _state()
    valid = {rd.ref_key for rd in state.verified}
    for section in state.sections:
        for claim in section["claims"]:
            assert set(claim["citation_ids"]) <= valid
    for row in state.comparison:
        assert set(row["citation_ids"]) <= valid
    for ex in state.extractions:
        assert ex["ref_key"] in valid
    # Scores and safety-matrix references are verified-only too.
    for s in state.scores["studies"]:
        assert s["ref_key"] in valid

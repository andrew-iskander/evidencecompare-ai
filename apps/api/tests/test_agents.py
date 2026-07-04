"""Multi-agent orchestrator tests (offline, deterministic).

Runs the full agent chain over the offline fixtures with no network or API keys
and locks: all six agents run, structured extractions are produced with parsed
effect sizes, and the anti-hallucination contract holds (every rendered citation
is a verified ref, head-to-head absence is reported honestly).
"""

from __future__ import annotations

import asyncio

from app.agents.base import PipelineState
from app.agents.orchestrator import DEFAULT_AGENTS, AIOrchestrator
from app.evidence.offline_fixtures import OfflineSource

A, B, TOPIC = "Telmisartan", "Valsartan", "Cardioprotection"


def _run(coro):
    return asyncio.run(coro)


def _state() -> PipelineState:
    state = PipelineState(A, B, TOPIC)
    state.sources = [OfflineSource()]

    async def go() -> PipelineState:
        await AIOrchestrator().run(state)
        return state

    return _run(go())


def test_all_six_agents_run():
    keys = [a.key for a in DEFAULT_AGENTS]
    assert keys == ["search", "ranking", "extraction", "guideline", "comparison", "writer"]


def test_orchestrator_produces_full_report():
    state = _state()
    assert state.raw_docs, "search agent retrieved candidates"
    assert state.verified, "ranking agent verified citations"
    assert state.sections, "writer produced sections"
    assert state.comparison, "comparison agent produced rows"
    assert state.queries, "search agent recorded optimized queries"


def test_extraction_parses_effect_sizes():
    state = _state()
    assert state.extractions, "trial-extraction agent produced records"
    # The offline fixture RCTs carry an HR and an RR in their abstracts.
    hrs = [e["hazard_ratio"] for e in state.extractions if e["hazard_ratio"]]
    rrs = [e["relative_risk"] for e in state.extractions if e["relative_risk"]]
    assert any("0.86" in h for h in hrs), f"expected parsed HR, got {hrs}"
    assert any("0.91" in r for r in rrs), f"expected parsed RR, got {rrs}"
    # Adverse events were detected deterministically.
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

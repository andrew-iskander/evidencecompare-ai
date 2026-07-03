"""Phase 3 RAG evidence-engine unit tests.

Exercises retrieval → ranking → verification → offline synthesis directly (no DB,
no network) and locks the anti-hallucination contract: only trusted sources are
retrieved, only verified docs are cited, no claim references an unknown citation,
and thin head-to-head evidence is reported honestly.
"""

from __future__ import annotations

import asyncio

from app.evidence.base import TRUSTED_SOURCES, RawDoc
from app.evidence.offline_fixtures import OfflineSource
from app.evidence.registry import retrieve_evidence
from app.llm.synthesizer import _sanitize, offline_synthesize
from app.rag.ranking import rank_docs
from app.rag.verifier import verify_doc

A, B, TOPIC = "Telmisartan", "Valsartan", "Cardioprotection"


def _run(coro):
    return asyncio.run(coro)


async def _pipeline() -> dict:
    docs = await retrieve_evidence(A, B, TOPIC, sources=[OfflineSource()])
    ranked = rank_docs(docs, [0.5] * len(docs))
    verified = [rd for rd in ranked if await verify_doc(rd.doc)]
    for i, rd in enumerate(verified):
        rd.ref_key = f"c{i + 1}"
    result = offline_synthesize(A, B, TOPIC, verified)
    result["_verified_refs"] = {rd.ref_key for rd in verified}
    return result


def test_retrieval_is_trusted_only():
    docs = _run(retrieve_evidence(A, B, TOPIC, sources=[OfflineSource()]))
    assert docs, "offline fixtures should return candidates"
    assert all(d.source in TRUSTED_SOURCES for d in docs)


def test_every_rendered_citation_is_verified():
    result = _run(_pipeline())
    valid = result["_verified_refs"]
    assert valid, "expected at least one verified citation"
    for section in result["sections"]:
        for claim in section["claims"]:
            assert set(claim["citation_ids"]) <= valid
    for row in result["comparison"]:
        assert set(row["citation_ids"]) <= valid


def test_no_head_to_head_reported_honestly():
    # Offline fixtures contain only single-molecule RCTs, so there is no direct
    # A-vs-B trial: the evidence-gaps section must own that gap.
    result = _run(_pipeline())
    gaps = next(s for s in result["sections"] if s["section_key"] == "evidence_gaps")
    assert gaps["insufficient_evidence"] is True
    assert "NOT" in gaps["claims"][0]["text"]


def test_ranking_prefers_higher_evidence_tier():
    meta = RawDoc(source="europepmc", title="m", study_design="meta_analysis", pmid="1")
    label = RawDoc(source="fda", title="l", study_design="drug_label", external_id="x")
    ranked = rank_docs([label, meta], [0.5, 0.5])  # equal relevance
    assert ranked[0].doc.study_design == "meta_analysis"


def test_sanitize_drops_invented_refs():
    data = {
        "sections": [{"claims": [{"text": "t", "citation_ids": ["c1", "c99"]}]}],
        "comparison": [{"citation_ids": ["c2", "made-up"]}],
    }
    _sanitize(data, {"c1", "c2"})
    assert data["sections"][0]["claims"][0]["citation_ids"] == ["c1"]
    assert data["comparison"][0]["citation_ids"] == ["c2"]

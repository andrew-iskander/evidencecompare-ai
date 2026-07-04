"""U2 tests: report caching, manual refresh, and living-evidence detection."""

from __future__ import annotations

import asyncio

from app.evidence.base import RawDoc
from app.evidence.offline_fixtures import OfflineSource
from app.services.freshness_service import significant_new
from app.services.report_service import normalize_query_key

_QUERY = {
    "molecule_a": "Olmesartan",
    "molecule_b": "Losartan",
    "topic": "Albuminuria",
}


def test_normalize_query_key_case_and_order():
    a = normalize_query_key("Telmisartan", "Valsartan", "Cardioprotection")
    b = normalize_query_key("  telmisartan ", "VALSARTAN", "cardioprotection")
    assert a == b, "case/whitespace should not change the key"
    # A/B order is meaningful (drives report columns) → distinct keys.
    assert a != normalize_query_key("Valsartan", "Telmisartan", "Cardioprotection")


def test_create_uses_cache_then_refresh_bypasses(client, auth_headers):
    first = client.post("/api/v1/reports", headers=auth_headers, json=_QUERY)
    assert first.status_code == 202, first.text
    fid = first.json()["id"]
    assert first.json()["cached"] is False

    # Same query, same user, within TTL → served from cache (same id).
    again = client.post("/api/v1/reports", headers=auth_headers, json=_QUERY)
    assert again.status_code == 202
    assert again.json()["cached"] is True
    assert again.json()["id"] == fid

    # refresh=true bypasses the cache → a brand-new report.
    forced = client.post(
        "/api/v1/reports", headers=auth_headers, json={**_QUERY, "refresh": True}
    )
    assert forced.json()["cached"] is False
    assert forced.json()["id"] != fid


def test_refresh_endpoint_creates_new_report(client, auth_headers):
    created = client.post("/api/v1/reports", headers=auth_headers, json=_QUERY).json()
    r = client.post(f"/api/v1/reports/{created['id']}/refresh", headers=auth_headers)
    assert r.status_code == 202, r.text
    assert r.json()["id"] != created["id"]
    assert r.json()["molecule_a"] == _QUERY["molecule_a"]


def test_check_updates_reports_up_to_date_offline(client, auth_headers):
    created = client.post("/api/v1/reports", headers=auth_headers, json=_QUERY).json()
    # Offline fixtures are static, so a completed report has no newer evidence.
    r = client.post(f"/api/v1/reports/{created['id']}/check-updates", headers=auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "up_to_date"
    assert body["new_items"] == 0


def test_significant_new_detects_high_tier():
    docs = asyncio.run(
        OfflineSource().search("Olmesartan", "Losartan", "Albuminuria", 12)
    )
    # Empty fingerprint → every high-tier study counts as new.
    fresh = significant_new(set(), docs)
    assert fresh, "expected high-tier offline docs to be flagged as new"
    tiers = {"rct", "meta_analysis", "systematic_review", "guideline", "trial_registry"}
    assert all(d.study_design in tiers for d in fresh)
    # A drug label is not a 'significant' new-evidence trigger.
    label = RawDoc(source="fda", title="label", study_design="drug_label", external_id="x")
    assert significant_new(set(), [label]) == []

    # Fingerprint covering all keys → nothing new.
    all_keys = {d.dedup_key() for d in docs}
    assert significant_new(all_keys, docs) == []

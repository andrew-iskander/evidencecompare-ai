"""Health endpoint exposes engine mode + live-readiness (no secrets)."""

from __future__ import annotations


def test_health_reports_modes(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    modes = body["modes"]
    # The suite runs offline with no keys.
    assert modes["evidence_mode"] == "offline"
    assert modes["llm_mode"] == "offline"
    assert modes["llm_live_ready"] is False
    assert modes["embeddings_live_ready"] is False

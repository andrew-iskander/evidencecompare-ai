from __future__ import annotations

import uuid


def _create_report(client, headers) -> dict:
    r = client.post(
        "/api/v1/reports",
        headers=headers,
        json={
            "molecule_a": "Telmisartan",
            "molecule_b": "Valsartan",
            "topic": "Cardioprotection",
        },
    )
    assert r.status_code == 202, r.text
    return r.json()


def test_report_lifecycle(client, auth_headers):
    created = _create_report(client, auth_headers)
    rid = created["id"]

    # eager pipeline → complete synchronously
    r = client.get(f"/api/v1/reports/{rid}", headers=auth_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "complete"
    assert body["molecule_a"] == "Telmisartan"
    # Offline test mode runs the real engine with the extractive synthesizer.
    assert body["model_synthesis"] == "offline-extractive"
    assert len(body["sections"]) >= 1
    assert len(body["comparison"]) >= 1
    assert len(body["citations"]) >= 1
    assert body["cost_usd"] >= 0  # offline synthesis is free; live Opus would be > 0

    # every rendered citation reference resolves to a verified citation
    ref_keys = {c["ref_key"] for c in body["citations"]}
    assert all(c["verified"] for c in body["citations"])
    for row in body["comparison"]:
        assert row["rationale"]  # Phase 4: every row explains its confidence
        for cid in row["citation_ids"]:
            assert cid in ref_keys
    for section in body["sections"]:
        for claim in section["claims"]:
            for cid in claim["citation_ids"]:
                assert cid in ref_keys

    # insufficient-evidence honesty is represented
    assert any(s.get("insufficient_evidence") for s in body["sections"])

    # Phase 5: citations carry a study design and per-molecule evidence is exposed
    assert any(c.get("study_design") for c in body["citations"])
    me = body["molecule_evidence"]
    assert me is not None
    assert set(me["a"]) == {"efficacy", "safety", "guideline"}
    assert set(me["b"]) == {"efficacy", "safety", "guideline"}


def test_report_list(client, auth_headers):
    _create_report(client, auth_headers)
    r = client.get("/api/v1/reports", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_report_stream(client, auth_headers):
    created = _create_report(client, auth_headers)
    rid = created["id"]
    # extract the raw token from the header
    token = auth_headers["Authorization"].split(" ", 1)[1]
    r = client.get(f"/api/v1/reports/{rid}/stream", params={"token": token})
    assert r.status_code == 200
    assert "text/event-stream" in r.headers["content-type"]
    text = r.text
    assert "event: status" in text
    assert "event: complete" in text


def test_export_markdown(client, auth_headers):
    created = _create_report(client, auth_headers)
    rid = created["id"]
    r = client.post(
        f"/api/v1/reports/{rid}/exports",
        headers=auth_headers,
        json={"format": "markdown"},
    )
    assert r.status_code == 201, r.text
    export = r.json()
    assert export["status"] == "ready"
    assert "# EvidenceCompare AI" in export["content"]
    assert "## References" in export["content"]


def test_report_ownership(client, auth_headers):
    created = _create_report(client, auth_headers)
    rid = created["id"]

    # a different user cannot read it
    r = client.post(
        "/api/v1/auth/register",
        json={"email": f"other_{uuid.uuid4().hex[:8]}@example.com", "password": "password123"},
    )
    other_email = r.json()["email"]
    other_token = client.post(
        "/api/v1/auth/login", json={"email": other_email, "password": "password123"}
    ).json()["access_token"]

    r = client.get(
        f"/api/v1/reports/{rid}", headers={"Authorization": f"Bearer {other_token}"}
    )
    assert r.status_code == 403


def test_report_not_found(client, auth_headers):
    r = client.get(f"/api/v1/reports/{uuid.uuid4()}", headers=auth_headers)
    assert r.status_code == 404


def test_report_delete(client, auth_headers):
    created = _create_report(client, auth_headers)
    rid = created["id"]
    assert client.delete(f"/api/v1/reports/{rid}", headers=auth_headers).status_code == 204
    assert client.get(f"/api/v1/reports/{rid}", headers=auth_headers).status_code == 404

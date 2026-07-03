from __future__ import annotations

import uuid


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_register_login_me_refresh(client):
    email = f"flow_{uuid.uuid4().hex[:8]}@example.com"

    r = client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
    assert r.status_code == 201, r.text
    assert r.json()["email"] == email

    # duplicate registration
    r = client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
    assert r.status_code == 409

    r = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    assert r.status_code == 200, r.text
    tokens = r.json()
    access, refresh = tokens["access_token"], tokens["refresh_token"]

    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access}"})
    assert r.status_code == 200
    assert r.json()["email"] == email

    r = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert r.status_code == 200
    assert r.json()["access_token"]


def test_bad_login(client):
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "wrongpass1"},
    )
    assert r.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_molecule_search(client):
    r = client.get("/api/v1/molecules/search", params={"q": "telmi"})
    assert r.status_code == 200
    names = [m["name"] for m in r.json()["results"]]
    assert "Telmisartan" in names

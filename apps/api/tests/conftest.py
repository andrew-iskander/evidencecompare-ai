from __future__ import annotations

import os
import pathlib

# Configure the environment BEFORE importing the app (settings are cached and the
# DB engine is created at import time).
_DB_PATH = pathlib.Path(__file__).parent / "_test.db"
os.environ.update(
    ENV="test",
    DATABASE_URL=f"sqlite+aiosqlite:///{_DB_PATH.as_posix()}",
    JWT_SECRET="test-secret",
    PIPELINE_MODE="eager",
    PIPELINE_STEP_DELAY="0",
    CORS_ORIGINS="http://localhost:3000",
    # Deterministic, network-free evidence engine for the suite: local fixtures +
    # offline extractive synthesis (no PubMed/Voyage/Claude calls).
    EVIDENCE_MODE="offline",
    LLM_MODE="offline",
)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(scope="session")
def client():
    if _DB_PATH.exists():
        _DB_PATH.unlink()
    from app.main import app

    with TestClient(app) as c:
        yield c

    # Release the SQLite file handle before cleanup (Windows locks open files).
    from app.db.session import engine

    engine.sync_engine.dispose()
    try:
        if _DB_PATH.exists():
            _DB_PATH.unlink()
    except PermissionError:
        pass


def _register_and_login(client: TestClient, email: str, password: str = "password123") -> str:
    client.post("/api/v1/auth/register", json={"email": email, "password": password})
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture
def auth_headers(client):
    import uuid

    token = _register_and_login(client, f"user_{uuid.uuid4().hex[:8]}@example.com")
    return {"Authorization": f"Bearer {token}"}

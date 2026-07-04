"""Export/download tests: every format returns a real, well-formed file."""

from __future__ import annotations


def _completed_report(client, headers) -> str:
    r = client.post(
        "/api/v1/reports",
        headers=headers,
        json={"molecule_a": "Aspirin", "molecule_b": "Clopidogrel", "topic": "Stroke prevention"},
    )
    assert r.status_code == 202, r.text
    rid = r.json()["id"]
    assert client.get(f"/api/v1/reports/{rid}", headers=headers).json()["status"] == "complete"
    return rid


# (format, leading magic bytes)
_SIGNATURES = [
    ("markdown", b"# EvidenceCompare AI"),
    ("pdf", b"%PDF"),
    ("xlsx", b"PK\x03\x04"),  # zip container
    ("pptx", b"PK\x03\x04"),  # zip container
]


def test_download_all_formats(client, auth_headers):
    rid = _completed_report(client, auth_headers)
    for fmt, magic in _SIGNATURES:
        r = client.get(
            f"/api/v1/reports/{rid}/download", params={"format": fmt}, headers=auth_headers
        )
        assert r.status_code == 200, f"{fmt}: {r.status_code}"
        assert r.content[: len(magic)] == magic, f"{fmt} magic bytes wrong"
        assert len(r.content) > 200, f"{fmt} suspiciously small"
        cd = r.headers["content-disposition"]
        assert "attachment" in cd and fmt_ext(fmt) in cd


def fmt_ext(fmt: str) -> str:
    return {"markdown": ".md", "pdf": ".pdf", "xlsx": ".xlsx", "pptx": ".pptx"}[fmt]


def test_download_rejects_bad_format(client, auth_headers):
    rid = _completed_report(client, auth_headers)
    r = client.get(
        f"/api/v1/reports/{rid}/download", params={"format": "docx"}, headers=auth_headers
    )
    assert r.status_code == 422  # not in the allowed Literal


def test_download_requires_auth(client, auth_headers):
    rid = _completed_report(client, auth_headers)
    r = client.get(f"/api/v1/reports/{rid}/download", params={"format": "pdf"})
    assert r.status_code == 401

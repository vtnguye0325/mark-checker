"""POST /llm-assess — Turnstile verification.

FastAPI resolves Depends before it parses the Pydantic body, so the dependency
is the first gate. A missing or empty token hits the dependency's 403 check
before Pydantic's 422 can fire, unless TURNSTILE_SECRET is unset, in which case
the 503 fires earlier still.
"""

from __future__ import annotations

from unittest.mock import patch


def test_analyze_missing_token_returns_403(
    client, analyze_payload, mock_turnstile_client, monkeypatch
):
    monkeypatch.setenv("TURNSTILE_SECRET", "dummy-secret")
    payload = {k: v for k, v in analyze_payload.items() if k != "turnstile_token"}
    with mock_turnstile_client(success=False):
        r = client.post("/llm-assess", json=payload)
    assert r.status_code == 403


def test_analyze_empty_token_returns_403(
    client, analyze_payload, mock_turnstile_client, monkeypatch
):
    monkeypatch.setenv("TURNSTILE_SECRET", "dummy-secret")
    with mock_turnstile_client(success=False):
        r = client.post("/llm-assess", json={**analyze_payload, "turnstile_token": ""})
    assert r.status_code == 403


def test_analyze_invalid_token_returns_403(
    client, analyze_payload, mock_turnstile_client, monkeypatch
):
    monkeypatch.setenv("TURNSTILE_SECRET", "dummy-secret")
    with mock_turnstile_client(success=False):
        r = client.post("/llm-assess", json=analyze_payload)
    assert r.status_code == 403


def test_analyze_no_secret_returns_503(client, analyze_payload, monkeypatch):
    monkeypatch.delenv("TURNSTILE_SECRET", raising=False)
    monkeypatch.delenv("DISABLE_TURNSTILE", raising=False)
    r = client.post("/llm-assess", json=analyze_payload)
    assert r.status_code == 503


def test_analyze_no_secret_disable_turnstile_bypasses(client, analyze_payload, monkeypatch):
    monkeypatch.delenv("TURNSTILE_SECRET", raising=False)
    monkeypatch.setenv("DISABLE_TURNSTILE", "true")
    with patch("mark_checker.api.analyze.analyze_trademark") as mock_analyze:
        mock_analyze.return_value = {"analysis": "Bypassed.", "sources": None}
        r = client.post("/llm-assess", json=analyze_payload)
    assert r.status_code == 200


def test_analyze_valid_token_returns_200(
    client, analyze_payload, mock_turnstile_client, monkeypatch
):
    monkeypatch.setenv("TURNSTILE_SECRET", "dummy-secret")
    with (
        mock_turnstile_client(success=True),
        patch("mark_checker.api.analyze.analyze_trademark") as mock_analyze,
    ):
        mock_analyze.return_value = {"analysis": "Test analysis.", "sources": None}
        r = client.post("/llm-assess", json=analyze_payload)
    assert r.status_code == 200
    assert "analysis" in r.json()

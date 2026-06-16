"""API-level tests using FastAPI TestClient."""

from __future__ import annotations
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

VALID_PAYLOAD = {
    "mark": "APPLE",
    "description": "computers and computer software",
    "nice_class": 9,
}


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------


def test_health_returns_200_or_503():
    # 200 when model is loaded, 503 while still warming up (correct behavior per item #3)
    r = client.get("/health")
    assert r.status_code in (200, 503)


def test_health_body():
    r = client.get("/health")
    assert r.json()["status"] in ("ok", "model_loading")


# ---------------------------------------------------------------------------
# POST /predict — happy path
# ---------------------------------------------------------------------------


def test_predict_returns_200():
    r = client.post("/predict", json=VALID_PAYLOAD)
    assert r.status_code == 200


def test_predict_response_has_required_fields():
    r = client.post("/predict", json=VALID_PAYLOAD)
    body = r.json()
    assert "label" in body
    assert "prob_distinctive" in body
    assert "prob_not_distinctive" in body
    assert "formatted_input" in body


def test_predict_label_is_valid():
    r = client.post("/predict", json=VALID_PAYLOAD)
    assert r.json()["label"] in {"distinctive", "not_distinctive"}


def test_predict_probs_are_floats_in_range():
    r = client.post("/predict", json=VALID_PAYLOAD)
    body = r.json()
    assert 0.0 <= body["prob_distinctive"] <= 1.0
    assert 0.0 <= body["prob_not_distinctive"] <= 1.0


def test_predict_formatted_input_is_string():
    r = client.post("/predict", json=VALID_PAYLOAD)
    assert isinstance(r.json()["formatted_input"], str)


def test_predict_with_optional_fields():
    payload = {**VALID_PAYLOAD, "translation": "la pomme", "pseudo_mark": "apple"}
    r = client.post("/predict", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert "la pomme" in body["formatted_input"]
    assert "apple" in body["formatted_input"]


# ---------------------------------------------------------------------------
# POST /predict — validation errors
# ---------------------------------------------------------------------------


def test_predict_missing_mark_returns_422():
    r = client.post("/predict", json={"description": "computers", "nice_class": 9})
    assert r.status_code == 422


def test_predict_missing_description_returns_422():
    r = client.post("/predict", json={"mark": "APPLE", "nice_class": 9})
    assert r.status_code == 422


def test_predict_missing_nice_class_returns_422():
    r = client.post("/predict", json={"mark": "APPLE", "description": "computers"})
    assert r.status_code == 422


def test_predict_nice_class_too_low_returns_422():
    r = client.post("/predict", json={**VALID_PAYLOAD, "nice_class": 0})
    assert r.status_code == 422


def test_predict_nice_class_too_high_returns_422():
    r = client.post("/predict", json={**VALID_PAYLOAD, "nice_class": 46})
    assert r.status_code == 422


def test_predict_empty_mark_returns_422():
    r = client.post("/predict", json={**VALID_PAYLOAD, "mark": ""})
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# POST /analyze — Turnstile verification
# ---------------------------------------------------------------------------

_ANALYZE_PAYLOAD = {
    "mark": "APPLE",
    "description": "computers and computer software",
    "nice_class": 9,
    "label": "distinctive",
    "prob_distinctive": 0.95,
    "attributions": [
        {"field": "Mark", "value": "APPLE", "attribution": 0.3},
    ],
    "turnstile_token": "test-token",
}


def _mock_turnstile_client(success: bool):
    """Return a context-manager patch for app.turnstile.httpx.AsyncClient.

    httpx's Response.json() and raise_for_status() are synchronous, so we use
    MagicMock for the response object and only AsyncMock for the awaitable post().
    """
    async def fake_post(*args, **kwargs):
        resp = MagicMock()
        resp.json.return_value = {"success": success}
        return resp

    instance = AsyncMock()
    instance.post = AsyncMock(side_effect=fake_post)

    mock_cls = MagicMock()
    mock_cls.return_value.__aenter__ = AsyncMock(return_value=instance)
    mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
    return patch("app.turnstile.httpx.AsyncClient", mock_cls)


# FastAPI resolves Depends before parsing the Pydantic body model, so the
# dependency is the first gate. Missing/empty token hits the dependency's 403
# check before Pydantic's 422 can fire (unless TURNSTILE_SECRET is unset, in
# which case the 503 fires even earlier).

def test_analyze_missing_token_returns_403(monkeypatch):
    monkeypatch.setenv("TURNSTILE_SECRET", "dummy-secret")
    payload = {k: v for k, v in _ANALYZE_PAYLOAD.items() if k != "turnstile_token"}
    with _mock_turnstile_client(success=False):
        r = client.post("/analyze", json=payload)
    assert r.status_code == 403


def test_analyze_empty_token_returns_403(monkeypatch):
    monkeypatch.setenv("TURNSTILE_SECRET", "dummy-secret")
    with _mock_turnstile_client(success=False):
        r = client.post("/analyze", json={**_ANALYZE_PAYLOAD, "turnstile_token": ""})
    assert r.status_code == 403


def test_analyze_invalid_token_returns_403(monkeypatch):
    monkeypatch.setenv("TURNSTILE_SECRET", "dummy-secret")
    with _mock_turnstile_client(success=False):
        r = client.post("/analyze", json=_ANALYZE_PAYLOAD)
    assert r.status_code == 403


def test_analyze_unconfigured_secret_returns_503(monkeypatch):
    monkeypatch.delenv("TURNSTILE_SECRET", raising=False)
    r = client.post("/analyze", json=_ANALYZE_PAYLOAD)
    assert r.status_code == 503


def test_analyze_valid_token_returns_200(monkeypatch):
    monkeypatch.setenv("TURNSTILE_SECRET", "dummy-secret")
    with _mock_turnstile_client(success=True), \
         patch("app.routes.analyze.analyze_trademark") as mock_analyze:
        mock_analyze.return_value = {"analysis": "Test analysis.", "sources": None}
        r = client.post("/analyze", json=_ANALYZE_PAYLOAD)
    assert r.status_code == 200
    assert "analysis" in r.json()

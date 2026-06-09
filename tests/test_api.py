"""API-level tests using FastAPI TestClient."""

from __future__ import annotations

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


def test_health_returns_200():
    r = client.get("/health")
    assert r.status_code == 200


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

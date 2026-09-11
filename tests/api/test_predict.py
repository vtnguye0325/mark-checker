"""POST /ml-predict.

The root conftest skips every test here whose name does not end in 422 when
backend/model/ is absent, because those cases need a loaded model.
"""

from __future__ import annotations


def test_predict_returns_200(client, predict_payload):
    r = client.post("/ml-predict", json=predict_payload)
    assert r.status_code == 200


def test_predict_response_has_required_fields(client, predict_payload):
    r = client.post("/ml-predict", json=predict_payload)
    body = r.json()
    assert "label" in body
    assert "prob_distinctive" in body
    assert "prob_not_distinctive" in body
    assert "formatted_input" in body


def test_predict_label_is_valid(client, predict_payload):
    r = client.post("/ml-predict", json=predict_payload)
    assert r.json()["label"] in {"distinctive", "not_distinctive"}


def test_predict_probs_are_floats_in_range(client, predict_payload):
    r = client.post("/ml-predict", json=predict_payload)
    body = r.json()
    assert 0.0 <= body["prob_distinctive"] <= 1.0
    assert 0.0 <= body["prob_not_distinctive"] <= 1.0


def test_predict_formatted_input_is_string(client, predict_payload):
    r = client.post("/ml-predict", json=predict_payload)
    assert isinstance(r.json()["formatted_input"], str)


def test_predict_with_optional_fields(client, predict_payload):
    payload = {**predict_payload, "translation": "la pomme", "pseudo_mark": "apple"}
    r = client.post("/ml-predict", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert "la pomme" in body["formatted_input"]
    assert "apple" in body["formatted_input"]


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


def test_predict_missing_mark_returns_422(client):
    r = client.post("/ml-predict", json={"description": "computers", "nice_class": 9})
    assert r.status_code == 422


def test_predict_missing_description_returns_422(client):
    r = client.post("/ml-predict", json={"mark": "APPLE", "nice_class": 9})
    assert r.status_code == 422


def test_predict_missing_nice_class_returns_422(client):
    r = client.post("/ml-predict", json={"mark": "APPLE", "description": "computers"})
    assert r.status_code == 422


def test_predict_nice_class_too_low_returns_422(client, predict_payload):
    r = client.post("/ml-predict", json={**predict_payload, "nice_class": 0})
    assert r.status_code == 422


def test_predict_nice_class_too_high_returns_422(client, predict_payload):
    r = client.post("/ml-predict", json={**predict_payload, "nice_class": 46})
    assert r.status_code == 422


def test_predict_empty_mark_returns_422(client, predict_payload):
    r = client.post("/ml-predict", json={**predict_payload, "mark": ""})
    assert r.status_code == 422

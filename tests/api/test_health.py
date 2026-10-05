"""GET /health."""

from __future__ import annotations


def test_health_returns_200_or_503(client):
    # 200 when the model is loaded, 503 while it still warms up.
    r = client.get("/health")
    assert r.status_code in (200, 503)


def test_health_body(client):
    r = client.get("/health")
    assert r.json()["status"] in ("ok", "model_loading")

"""Fixtures that every route test shares.

``mark_checker.main`` loads the .env that ``mark_checker.core.auth`` reads at
import, so import ``main`` before any other package module.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import openai
import pytest
from fastapi.testclient import TestClient

from mark_checker.main import app  # noqa: I001
from mark_checker.core.auth import SessionUser, current_user
from mark_checker.core.db import get_session
from mark_checker.core.limiter import limiter


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def _auth_and_db_overrides():
    """Batch C put a session and a database write on the three check routes.

    The API tests have no Postgres and no Google sign-in, so override
    ``current_user`` with a fixed user and ``get_session`` with a session whose
    writes are no-ops. ``update_query_stage`` reads ``result.rowcount``, so the
    fake ``execute`` returns a row count of 1.
    """
    test_user = SessionUser(id=uuid.uuid4(), email="test@example.com")

    class _FakeSession:
        def add(self, _obj):
            pass

        async def commit(self):
            pass

        async def rollback(self):
            pass

        async def execute(self, *_args, **_kwargs):
            result = MagicMock()
            result.rowcount = 1
            return result

    async def _fake_get_session():
        yield _FakeSession()

    app.dependency_overrides[current_user] = lambda: test_user
    app.dependency_overrides[get_session] = _fake_get_session
    yield
    app.dependency_overrides.pop(current_user, None)
    app.dependency_overrides.pop(get_session, None)


@pytest.fixture
def predict_payload() -> dict:
    return {
        "mark": "APPLE",
        "description": "computers and computer software",
        "nice_class": 9,
    }


@pytest.fixture
def analyze_payload(predict_payload) -> dict:
    return {
        **predict_payload,
        "label": "distinctive",
        "prob_distinctive": 0.95,
        "attributions": [
            {"field": "Mark", "value": "APPLE", "attribution": 0.3},
        ],
        "turnstile_token": "test-token",
    }


@pytest.fixture
def mock_turnstile_client():
    """Return a factory for a context-manager patch of the Turnstile client.

    httpx's ``Response.json()`` and ``raise_for_status()`` are synchronous, so
    the response object is a MagicMock and only the awaitable ``post()`` is an
    AsyncMock.
    """

    def _factory(success: bool):
        async def fake_post(*_args, **_kwargs):
            resp = MagicMock()
            resp.json.return_value = {"success": success}
            return resp

        instance = AsyncMock()
        instance.post = AsyncMock(side_effect=fake_post)

        mock_cls = MagicMock()
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=instance)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)
        return patch("mark_checker.core.turnstile.httpx.AsyncClient", mock_cls)

    return _factory


@pytest.fixture
def rate_limit_error():
    """Return a factory for an ``openai.RateLimitError`` with a Retry-After."""

    def _factory(message: str) -> openai.RateLimitError:
        response = httpx.Response(
            429,
            headers={"retry-after": "42"},
            request=httpx.Request("POST", "https://provider.example/v1/chat"),
        )
        return openai.RateLimitError(message, response=response, body=None)

    return _factory


@pytest.fixture
def post_analyze_raising(client, analyze_payload, monkeypatch):
    """Return a caller that posts /llm-assess with the analysis raising ``exc``.

    The analyze route stacks an account limit and an IP limit, and the other
    tests in the suite spend part of that quota, so reset the counters or
    slowapi answers 429 before the provider error under test can.
    """

    def _post(exc: Exception):
        limiter.reset()
        monkeypatch.delenv("TURNSTILE_SECRET", raising=False)
        monkeypatch.setenv("DISABLE_TURNSTILE", "true")
        with patch("mark_checker.api.analyze.analyze_trademark", side_effect=exc):
            return client.post("/llm-assess", json=analyze_payload)

    return _post


@pytest.fixture
def history_row():
    """Return a factory for one fake ``queries`` row."""

    def _factory(**over):
        base = dict(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            created_at=datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
            mark="ACME",
            description="widgets",
            nice_class=9,
            translation="",
            pseudo_mark="",
            label="distinctive",
            prob_distinctive=0.81,
            formatted_input="ACME | widgets",
            attributions=[{"field": "Mark", "attribution": 0.2}],
            analysis="Looks strong.",
            sources={"tmep": [], "ttab": []},
            analysis_error=None,
        )
        base.update(over)
        return SimpleNamespace(**base)

    return _factory

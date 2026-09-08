"""GET /history and GET /history/{query_id}.

The autouse fixture in conftest overrides ``get_session`` with a fake whose
``execute`` returns a bare ``MagicMock``. The history route calls
``.scalars().all()`` and ``.scalar_one_or_none()``, so each test here installs
its own session override that returns the rows the test needs.
"""

from __future__ import annotations

import socket
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.main import app  # noqa: I001  (loads .env before app.auth reads SESSION_SECRET)
from app.auth import SessionUser, current_user
from app.db import get_session

_client = TestClient(app)


def _row(**over):
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
    )
    base.update(over)
    return SimpleNamespace(**base)


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return self

    def all(self):
        return list(self._rows)

    def scalar_one_or_none(self):
        return self._rows[0] if self._rows else None


# Connection failures that a real Postgres outage raises. asyncpg raises bare
# OSError subclasses (never a SQLAlchemyError) when it cannot reach the server,
# plus OperationalError once a pool connection drops mid-query.
DB_DOWN_ERRORS = [
    ConnectionRefusedError("connection refused"),
    socket.gaierror("nodename nor servname provided"),
    TimeoutError("timed out"),
    OperationalError("x", {}, Exception()),
]


def _session_returning(rows, raises=None, sink=None):
    class _S:
        async def execute(self, stmt, *_a, **_k):
            if sink is not None:
                sink.append(stmt)
            if raises is not None:
                raise raises
            return _Result(rows)

        async def commit(self):
            pass

        async def rollback(self):
            pass

    async def _dep():
        yield _S()

    return _dep


@pytest.fixture
def user_id():
    uid = uuid.uuid4()
    app.dependency_overrides[current_user] = lambda: SessionUser(id=uid, email="a@b.com")
    yield uid
    # The autouse conftest fixture pops the key after this; nothing to restore.


def test_list_returns_summary_fields(user_id):
    rows = [_row(user_id=user_id), _row(user_id=user_id)]
    app.dependency_overrides[get_session] = _session_returning(rows)
    resp = _client.get("/history")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    assert set(body[0]) == {"id", "created_at", "mark", "nice_class", "label", "prob_distinctive"}


def test_list_caps_limit_at_100(user_id):
    app.dependency_overrides[get_session] = _session_returning([])
    assert _client.get("/history?limit=500").status_code == 422
    assert _client.get("/history?limit=100").status_code == 200


@pytest.mark.parametrize("exc", DB_DOWN_ERRORS, ids=lambda e: type(e).__name__)
def test_list_database_down_returns_503(user_id, exc):
    app.dependency_overrides[get_session] = _session_returning([], raises=exc)
    resp = _client.get("/history")
    assert resp.status_code == 503
    assert resp.json()["detail"] == "History is unavailable right now."


@pytest.mark.parametrize("exc", DB_DOWN_ERRORS, ids=lambda e: type(e).__name__)
def test_record_database_down_returns_503(user_id, exc):
    app.dependency_overrides[get_session] = _session_returning([], raises=exc)
    resp = _client.get(f"/history/{uuid.uuid4()}")
    assert resp.status_code == 503
    assert resp.json()["detail"] == "History is unavailable right now."


def test_list_filters_by_caller_user_id(user_id):
    """The user_id filter must be in the SQL, not applied after the fetch."""
    seen = []
    app.dependency_overrides[get_session] = _session_returning([], sink=seen)
    assert _client.get("/history").status_code == 200
    sql = str(seen[0].compile(compile_kwargs={"literal_binds": True}))
    assert "user_id" in sql
    assert user_id.hex in sql.replace("-", "")


def test_record_filters_by_caller_user_id(user_id):
    seen = []
    row = _row(user_id=user_id)
    app.dependency_overrides[get_session] = _session_returning([row], sink=seen)
    assert _client.get(f"/history/{row.id}").status_code == 200
    sql = str(seen[0].compile(compile_kwargs={"literal_binds": True}))
    assert "user_id" in sql
    assert user_id.hex in sql.replace("-", "")


def test_record_returns_full_row(user_id):
    row = _row(user_id=user_id)
    app.dependency_overrides[get_session] = _session_returning([row])
    resp = _client.get(f"/history/{row.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["analysis"] == "Looks strong."
    assert body["attributions"] == [{"field": "Mark", "attribution": 0.2}]


def test_record_foreign_or_missing_returns_404(user_id):
    app.dependency_overrides[get_session] = _session_returning([])
    resp = _client.get(f"/history/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_record_bad_uuid_returns_404(user_id):
    app.dependency_overrides[get_session] = _session_returning([_row()])
    resp = _client.get("/history/not-a-uuid")
    assert resp.status_code == 404

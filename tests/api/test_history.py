"""GET /history and GET /history/{query_id}.

The autouse fixture in conftest overrides ``get_session`` with a fake whose
``execute`` returns a bare ``MagicMock``. The history route calls
``.scalars().all()`` and ``.scalar_one_or_none()``, so each test here installs
its own session override that returns the rows the test needs.
"""

from __future__ import annotations

import socket
import uuid

import pytest
from sqlalchemy.exc import OperationalError

from mark_checker.core.auth import SessionUser, current_user
from mark_checker.core.db import get_session
from mark_checker.main import app


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


def test_list_returns_summary_fields(client, history_row, user_id):
    rows = [history_row(user_id=user_id), history_row(user_id=user_id)]
    app.dependency_overrides[get_session] = _session_returning(rows)
    resp = client.get("/history")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 2
    assert set(body[0]) == {"id", "created_at", "mark", "nice_class", "label", "prob_distinctive"}


def test_list_caps_limit_at_100(client, user_id):
    app.dependency_overrides[get_session] = _session_returning([])
    assert client.get("/history?limit=500").status_code == 422
    assert client.get("/history?limit=100").status_code == 200


@pytest.mark.parametrize("exc", DB_DOWN_ERRORS, ids=lambda e: type(e).__name__)
def test_list_database_down_returns_503(client, user_id, exc):
    app.dependency_overrides[get_session] = _session_returning([], raises=exc)
    resp = client.get("/history")
    assert resp.status_code == 503
    assert resp.json()["detail"] == "History is unavailable right now."


@pytest.mark.parametrize("exc", DB_DOWN_ERRORS, ids=lambda e: type(e).__name__)
def test_record_database_down_returns_503(client, user_id, exc):
    app.dependency_overrides[get_session] = _session_returning([], raises=exc)
    resp = client.get(f"/history/{uuid.uuid4()}")
    assert resp.status_code == 503
    assert resp.json()["detail"] == "History is unavailable right now."


def test_list_filters_by_caller_user_id(client, user_id):
    """The user_id filter must be in the SQL, not applied after the fetch."""
    seen = []
    app.dependency_overrides[get_session] = _session_returning([], sink=seen)
    assert client.get("/history").status_code == 200
    sql = str(seen[0].compile(compile_kwargs={"literal_binds": True}))
    assert "user_id" in sql
    assert user_id.hex in sql.replace("-", "")


def test_record_filters_by_caller_user_id(client, history_row, user_id):
    seen = []
    row = history_row(user_id=user_id)
    app.dependency_overrides[get_session] = _session_returning([row], sink=seen)
    assert client.get(f"/history/{row.id}").status_code == 200
    sql = str(seen[0].compile(compile_kwargs={"literal_binds": True}))
    assert "user_id" in sql
    assert user_id.hex in sql.replace("-", "")


def test_record_returns_full_row(client, history_row, user_id):
    row = history_row(user_id=user_id)
    app.dependency_overrides[get_session] = _session_returning([row])
    resp = client.get(f"/history/{row.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["analysis"] == "Looks strong."
    assert body["attributions"] == [{"field": "Mark", "attribution": 0.2}]


def test_record_foreign_or_missing_returns_404(client, user_id):
    app.dependency_overrides[get_session] = _session_returning([])
    resp = client.get(f"/history/{uuid.uuid4()}")
    assert resp.status_code == 404


def test_record_bad_uuid_returns_404(client, history_row, user_id):
    app.dependency_overrides[get_session] = _session_returning([history_row()])
    resp = client.get("/history/not-a-uuid")
    assert resp.status_code == 404

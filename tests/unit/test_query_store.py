"""update_query_stage must swallow every database failure.

The callers run after a paid LLM call. If a database error escapes, it masks
the provider error that the caller is in the middle of reporting, and the user
gets a 500 in place of the mapped 429 or 503.
"""

from __future__ import annotations

import socket
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import OperationalError

from mark_checker.services.query_store import update_query_stage

# An unreachable Postgres makes asyncpg raise these bare OSError subclasses,
# outside the SQLAlchemy hierarchy. OperationalError is the SQLAlchemy case.
DB_DOWN_ERRORS = [
    ConnectionRefusedError("connection refused"),
    socket.gaierror("name resolution failed"),
    TimeoutError("timed out"),
    OperationalError("SELECT 1", {}, Exception("closed")),
]


def _session(exc: Exception | None = None, rollback_exc: Exception | None = None) -> MagicMock:
    session = MagicMock()
    result = MagicMock()
    result.rowcount = 1
    session.execute = AsyncMock(return_value=result, side_effect=exc)
    session.commit = AsyncMock()
    session.rollback = AsyncMock(side_effect=rollback_exc)
    return session


@pytest.mark.asyncio
@pytest.mark.parametrize("exc", DB_DOWN_ERRORS, ids=lambda e: type(e).__name__)
async def test_database_error_does_not_escape(exc):
    session = _session(exc)
    await update_query_stage(session, str(uuid.uuid4()), uuid.uuid4(), {"analysis": None})
    session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_a_failed_rollback_does_not_escape():
    """A dead connection fails the rollback too."""
    session = _session(ConnectionRefusedError(), rollback_exc=ConnectionRefusedError())
    await update_query_stage(session, str(uuid.uuid4()), uuid.uuid4(), {"analysis": None})


@pytest.mark.asyncio
async def test_a_bad_query_id_returns_before_the_database():
    session = _session()
    await update_query_stage(session, "not-a-uuid", uuid.uuid4(), {"analysis": None})
    session.execute.assert_not_awaited()

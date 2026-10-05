from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import (
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)

# Fail closed, in the same style as TURNSTILE_SECRET. A silent deploy with no
# database is worse than a loud crash at import.
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is unset. Set it before you start the backend.")

# pool_pre_ping drops connections that Postgres closed while the backend was idle.
engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_session():
    """Yield one session per request."""
    async with AsyncSessionLocal() as session:
        yield session


# asyncpg SQLSTATEs that a retry can never fix: bad password, bad auth,
# unknown database. Stop on the first one instead of waiting out 10 rounds.
_FATAL_SQLSTATES = {"28P01", "28000", "3D000"}

# backend/alembic, two levels up from mark_checker/core/db.py. The backend is
# installed in editable mode, so this path resolves inside the container too.
_ALEMBIC_DIR = Path(__file__).resolve().parents[2] / "alembic"
_ALEMBIC_INI = _ALEMBIC_DIR.parent / "alembic.ini"

# The revision that holds the schema as it stood before Alembic. A database
# created by the old create_all path already has those tables, so stamp it with
# this revision rather than replay it.
_BASELINE_REVISION = "0001_baseline"


def _alembic_config(connection):
    """Build an Alembic config that runs on an open connection."""
    from alembic.config import Config

    config = Config(str(_ALEMBIC_INI))
    config.set_main_option("script_location", str(_ALEMBIC_DIR))
    config.attributes["connection"] = connection
    return config


def _run_migrations(connection) -> None:
    """Bring the schema up to head on the given sync connection.

    Alembic owns the schema. A database that predates Alembic has the tables but
    no alembic_version row, and an unstamped upgrade would try to rebuild live
    tables, so stamp the baseline first and let the later revisions run.
    """
    from alembic import command

    config = _alembic_config(connection)
    table_names = inspect(connection).get_table_names()
    if "alembic_version" not in table_names and "queries" in table_names:
        logger.info("init_models: database predates Alembic, stamping %s", _BASELINE_REVISION)
        command.stamp(config, _BASELINE_REVISION)
    command.upgrade(config, "head")


async def init_models() -> None:
    """Bring the schema to the head Alembic revision.

    Postgres can pass its healthcheck a moment before it accepts connections, so
    retry up to 10 times, 2 seconds apart, then re-raise.
    """
    from sqlalchemy.exc import OperationalError

    from mark_checker.core import models  # noqa: F401  (register the ORM classes on Base)

    last_error: Exception | None = None
    for attempt in range(1, 11):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(_run_migrations)
            return
        except (OSError, OperationalError) as exc:
            last_error = exc
            sqlstate = (
                getattr(exc.orig, "sqlstate", None) if isinstance(exc, OperationalError) else None
            )
            if sqlstate in _FATAL_SQLSTATES:
                logger.error("init_models: unrecoverable database error (SQLSTATE %s)", sqlstate)
                raise
            is_last = attempt == 10
            logger.warning(
                "init_models attempt %d/10 failed: %s",
                attempt,
                exc,
                exc_info=is_last,
            )
            if not is_last:
                await asyncio.sleep(2)
    raise RuntimeError("init_models failed after 10 attempts") from last_error

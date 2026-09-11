"""Alembic environment for the mark_checker schema.

The app runs on an async driver (``postgresql+asyncpg``), so the online path
opens an ``AsyncEngine`` and drives the migrations through ``run_sync``. The app
itself calls ``run_migrations`` in ``mark_checker.core.db`` on an existing
connection; this file is what the ``alembic`` command line uses.
"""

from __future__ import annotations

import asyncio
import os
from logging.config import fileConfig

from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from mark_checker.core import models  # noqa: F401  (register the ORM classes on Base)
from mark_checker.core.db import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _database_url() -> str:
    """Return the URL for the migrations, or raise when it is unset."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is unset. Set it before you run alembic.")
    return url


def run_migrations_offline() -> None:
    """Emit the SQL for the migrations without a database connection."""
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def _run(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online_async() -> None:
    """Open an async engine and run the migrations on it."""
    engine = create_async_engine(_database_url(), poolclass=None)
    async with engine.begin() as connection:
        await connection.run_sync(_run)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    # mark_checker.core.db hands its own live connection through this attribute,
    # so the app reuses one engine instead of opening a second one at startup.
    connectable = config.attributes.get("connection", None)
    if connectable is not None:
        _run(connectable)
    else:
        asyncio.run(run_migrations_online_async())

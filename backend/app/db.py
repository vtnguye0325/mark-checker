from __future__ import annotations

import asyncio
import logging
import os

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


async def init_models() -> None:
    """Create the tables from SQLAlchemy metadata.

    Postgres can pass its healthcheck a moment before it accepts connections, so
    retry up to 10 times, 2 seconds apart, then re-raise.
    """
    from sqlalchemy.exc import OperationalError

    from app import models  # noqa: F401  (register the ORM classes on Base)

    last_error: Exception | None = None
    for attempt in range(1, 11):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            return
        except (OSError, OperationalError) as exc:
            last_error = exc
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

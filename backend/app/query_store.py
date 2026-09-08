from __future__ import annotations

import logging
import uuid

from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Query

log = logging.getLogger(__name__)


async def update_query_stage(
    session: AsyncSession,
    query_id: str | None,
    user_id: uuid.UUID,
    values: dict,
) -> None:
    """Write one stage's results onto an existing query row.

    The ``WHERE`` clause carries ``user_id``, so one user can never write into
    another user's row. A missing row, a foreign row, or a database error all
    log and return — stage 2 and stage 3 already cost a paid LLM call, so the
    user must still get the answer.
    """
    if not query_id:
        return
    try:
        row_id = uuid.UUID(str(query_id))
    except (ValueError, TypeError):
        log.warning("update_query_stage: bad query_id %r", query_id)
        return
    try:
        result = await session.execute(
            update(Query).where(Query.id == row_id, Query.user_id == user_id).values(**values)
        )
        await session.commit()
    except SQLAlchemyError as exc:
        await session.rollback()
        log.error("update_query_stage: database error for query_id %s: %s", row_id, exc)
        return
    if result.rowcount == 0:
        log.warning("update_query_stage: no row for query_id %s and user %s", row_id, user_id)

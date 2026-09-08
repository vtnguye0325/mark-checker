from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi import Query as QueryParam
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import SessionUser, current_user
from app.db import get_session
from app.limiter import DEFAULT_LIMIT, limiter
from app.models import Query

log = logging.getLogger(__name__)
router = APIRouter(prefix="/history", tags=["history"])

_UNAVAILABLE = "History is unavailable right now."

# get_session opens no connection at entry, so the first connect happens inside
# session.execute. When Postgres is unreachable, asyncpg raises a bare OSError
# (ConnectionRefusedError, socket.gaierror, TimeoutError) that never reaches the
# SQLAlchemy hierarchy. init_models catches (OSError, OperationalError) for the
# same reason. Catch both here so the outage maps to a 503, not a bare 500.
_DB_DOWN = (SQLAlchemyError, OSError)


class HistoryItem(BaseModel):
    id: str
    created_at: str
    mark: str
    nice_class: int
    label: str | None = None
    prob_distinctive: float | None = None


class HistoryRecord(BaseModel):
    id: str
    created_at: str
    mark: str
    description: str
    nice_class: int
    translation: str
    pseudo_mark: str
    label: str | None = None
    prob_distinctive: float | None = None
    formatted_input: str | None = None
    attributions: list | dict | None = None
    analysis: str | None = None
    sources: list | dict | None = None


@router.get("", response_model=list[HistoryItem])
@limiter.limit(DEFAULT_LIMIT)
async def list_history(
    request: Request,  # noqa: ARG001  (slowapi reads the client IP off this)
    limit: int = QueryParam(50, ge=1, le=100),
    offset: int = QueryParam(0, ge=0),
    user: SessionUser = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> list[HistoryItem]:
    """Return the caller's own checks, newest first, with summary fields only.

    The ``WHERE`` clause carries ``user_id``, so the list never shows another
    user's checks. current_user reads no database, so this route stays usable
    for the identity check even when Postgres is down; only the query below
    fails, and it maps to a 503.
    """
    stmt = (
        select(Query)
        .where(Query.user_id == user.id)
        .order_by(Query.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    try:
        rows = (await session.execute(stmt)).scalars().all()
    except _DB_DOWN as exc:
        log.error("list_history: database error for user %s: %s", user.id, exc)
        raise HTTPException(status_code=503, detail=_UNAVAILABLE) from exc

    return [
        HistoryItem(
            id=str(row.id),
            created_at=row.created_at.isoformat(),
            mark=row.mark,
            nice_class=row.nice_class,
            label=row.label,
            prob_distinctive=row.prob_distinctive,
        )
        for row in rows
    ]


@router.get("/{query_id}", response_model=HistoryRecord)
@limiter.limit(DEFAULT_LIMIT)
async def get_history_record(
    request: Request,  # noqa: ARG001
    query_id: str,
    user: SessionUser = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> HistoryRecord:
    """Return one full row, filtered by ``user_id``.

    A bad id, a missing row, and a row that belongs to another user all return
    404. The filter is in the query, so the endpoint never confirms that an id
    exists for somebody else.
    """
    try:
        row_id = uuid.UUID(query_id)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=404, detail="No such record.") from exc

    stmt = select(Query).where(Query.id == row_id, Query.user_id == user.id)
    try:
        row = (await session.execute(stmt)).scalar_one_or_none()
    except _DB_DOWN as exc:
        log.error("get_history_record: database error for user %s: %s", user.id, exc)
        raise HTTPException(status_code=503, detail=_UNAVAILABLE) from exc

    if row is None:
        raise HTTPException(status_code=404, detail="No such record.")

    return HistoryRecord(
        id=str(row.id),
        created_at=row.created_at.isoformat(),
        mark=row.mark,
        description=row.description,
        nice_class=row.nice_class,
        translation=row.translation,
        pseudo_mark=row.pseudo_mark,
        label=row.label,
        prob_distinctive=row.prob_distinctive,
        formatted_input=row.formatted_input,
        attributions=row.attributions,
        analysis=row.analysis,
        sources=row.sources,
    )

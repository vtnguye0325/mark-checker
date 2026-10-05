from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from mark_checker.core.auth import SessionUser, current_user
from mark_checker.core.db import get_session
from mark_checker.core.limiter import DEFAULT_LIMIT, limiter
from mark_checker.core.models import Query
from mark_checker.schemas.analysis import PredictRequest, PredictResponse
from mark_checker.services.model_service import predict_one
from mark_checker.services.text_formatter import format_mark

log = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ml-predict", response_model=PredictResponse)
@limiter.limit(DEFAULT_LIMIT)
async def predict(
    request: Request,  # noqa: ARG001  (slowapi reads the client IP off this)
    req: PredictRequest,
    user: SessionUser = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> PredictResponse:
    fmt = format_mark(
        mark=req.mark,
        description=req.description,
        nice_class=req.nice_class,
        translation=req.translation,
        pseudo_mark=req.pseudo_mark,
    )
    # predict_one is CPU-bound. run_in_threadpool keeps it off the event loop,
    # the same behavior FastAPI gave a plain `def` route.
    result = await run_in_threadpool(predict_one, fmt.text)

    row = Query(
        id=uuid.uuid4(),
        user_id=user.id,
        mark=req.mark,
        description=req.description,
        nice_class=req.nice_class,
        translation=req.translation,
        pseudo_mark=req.pseudo_mark,
        label=result["label"],
        prob_distinctive=result["prob_distinctive"],
        formatted_input=fmt.text,
    )
    session.add(row)
    try:
        await session.commit()
    # An unreachable Postgres makes asyncpg raise a bare OSError subclass
    # outside the SQLAlchemy hierarchy, so the catch names OSError as well.
    except (SQLAlchemyError, OSError) as exc:
        try:
            await session.rollback()
        except (SQLAlchemyError, OSError) as rollback_exc:
            log.error("ml-predict: rollback failed: %s", rollback_exc)
        log.error("ml-predict: failed to save the query row: %s", exc)
        raise HTTPException(status_code=503, detail="Cannot save your check right now") from exc

    return PredictResponse(**result, formatted_input=fmt.text, query_id=str(row.id))

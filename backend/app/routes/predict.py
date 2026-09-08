from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.auth import SessionUser, current_user
from app.db import get_session
from app.limiter import DEFAULT_LIMIT, limiter
from app.models import Query
from app.services.model_service import predict_one
from app.services.text_formatter import format_mark

log = logging.getLogger(__name__)
router = APIRouter()


class PredictRequest(BaseModel):
    mark: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    nice_class: int = Field(..., ge=1, le=45)
    translation: str = Field("", max_length=200)
    pseudo_mark: str = Field("", max_length=200)


class PredictResponse(BaseModel):
    label: str
    prob_distinctive: float
    prob_not_distinctive: float
    formatted_input: str
    query_id: str


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
    except SQLAlchemyError as exc:
        await session.rollback()
        log.error("ml-predict: failed to save the query row: %s", exc)
        raise HTTPException(status_code=503, detail="Cannot save your check right now") from exc

    return PredictResponse(**result, formatted_input=fmt.text, query_id=str(row.id))

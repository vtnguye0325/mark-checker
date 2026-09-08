from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.auth import SessionUser, current_user
from app.db import get_session
from app.limiter import DEFAULT_LIMIT, limiter
from app.query_store import update_query_stage
from app.services.model_service import explain_one
from app.services.text_formatter import format_mark

router = APIRouter()


class ExplainRequest(BaseModel):
    mark: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    nice_class: int = Field(..., ge=1, le=45)
    translation: str = Field("", max_length=200)
    pseudo_mark: str = Field("", max_length=200)
    query_id: str | None = Field(None, max_length=64)


class Attribution(BaseModel):
    field: str = Field(..., max_length=64)
    value: str = Field(..., max_length=2000)
    attribution: float


class ExplainResponse(BaseModel):
    label: str
    prob_distinctive: float
    prob_not_distinctive: float
    formatted_input: str
    attributions: list[Attribution]


@router.post("/llm-explain", response_model=ExplainResponse)
@limiter.limit(DEFAULT_LIMIT)
async def explain(
    request: Request,  # noqa: ARG001  (slowapi reads the client IP off this)
    req: ExplainRequest,
    user: SessionUser = Depends(current_user),
    session: AsyncSession = Depends(get_session),
) -> ExplainResponse:
    fmt = format_mark(
        mark=req.mark,
        description=req.description,
        nice_class=req.nice_class,
        translation=req.translation,
        pseudo_mark=req.pseudo_mark,
    )
    # explain_one is CPU-bound. Keep it off the event loop.
    result = await run_in_threadpool(explain_one, list(fmt.fields))

    await update_query_stage(
        session, req.query_id, user.id, {"attributions": result["attributions"]}
    )

    return ExplainResponse(**result, formatted_input=fmt.text)

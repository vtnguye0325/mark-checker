from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from mark_checker.core.auth import SessionUser, current_user
from mark_checker.core.db import get_session
from mark_checker.core.limiter import DEFAULT_LIMIT, limiter
from mark_checker.schemas.analysis import ExplainRequest, ExplainResponse
from mark_checker.services.model_service import explain_one
from mark_checker.services.query_store import update_query_stage
from mark_checker.services.text_formatter import format_mark

router = APIRouter()


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

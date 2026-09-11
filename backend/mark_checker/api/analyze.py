from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from mark_checker.core.auth import SessionUser, current_user
from mark_checker.core.db import get_session
from mark_checker.core.limiter import ANALYZE_IP_LIMIT, ANALYZE_USER_LIMIT, _session_key, limiter
from mark_checker.core.turnstile import verify_turnstile
from mark_checker.schemas.analysis import AnalyzeRequest, AnalyzeResponse
from mark_checker.services.analysis import analyze_trademark
from mark_checker.services.query_store import update_query_stage

log = logging.getLogger(__name__)
router = APIRouter()


@router.post("/llm-assess", response_model=AnalyzeResponse)
# The account limit is the real cap; the IP limit is the backstop against one
# machine registering many accounts. current_user runs first and has stashed the
# user on request.state by the time _session_key reads it.
@limiter.limit(ANALYZE_USER_LIMIT, key_func=_session_key)
@limiter.limit(ANALYZE_IP_LIMIT)
async def analyze(
    request: Request,  # noqa: ARG001
    req: AnalyzeRequest,
    user: SessionUser = Depends(current_user),
    session: AsyncSession = Depends(get_session),
    _: None = Depends(verify_turnstile),
) -> AnalyzeResponse:
    log.info("llm-assess request  mark=%r class=%d label=%s", req.mark, req.nice_class, req.label)
    try:
        # analyze_trademark blocks: an LLM call plus ChromaDB retrieval. This
        # route is async, so run it in the threadpool or it stalls the event
        # loop, and one uvicorn worker means the whole backend stalls with it.
        # An openai.APIError goes to the handler in core/llm_errors.py.
        result = await run_in_threadpool(
            analyze_trademark,
            mark=req.mark,
            description=req.description,
            nice_class=req.nice_class,
            label=req.label,
            prob_distinctive=req.prob_distinctive,
            attributions=[a.model_dump() for a in req.attributions],
        )
    except RuntimeError as exc:
        log.error("analyze failed: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    await update_query_stage(
        session,
        req.query_id,
        user.id,
        {"analysis": result["analysis"], "sources": result.get("sources")},
    )

    return AnalyzeResponse(
        analysis=result["analysis"],
        sources=result.get("sources"),
    )

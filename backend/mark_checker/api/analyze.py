from __future__ import annotations

import logging

import openai
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from mark_checker.core.auth import SessionUser, current_user
from mark_checker.core.db import get_session
from mark_checker.core.limiter import ANALYZE_IP_LIMIT, ANALYZE_USER_LIMIT, _session_key, limiter
from mark_checker.core.llm_errors import llm_error_detail
from mark_checker.core.turnstile import verify_turnstile
from mark_checker.schemas.analysis import AnalyzeRequest, AnalyzeResponse
from mark_checker.services.analysis import analyze_trademark
from mark_checker.services.query_store import update_query_stage

log = logging.getLogger(__name__)
router = APIRouter()

# What the history page shows for a stage-3 RuntimeError. The raw message names
# internals, so it goes to the log only.
_RUNTIME_FAILURE_DETAIL = "The analysis service is unavailable. Run the check again."


async def _mark_analysis_failed(
    session: AsyncSession,
    req: AnalyzeRequest,
    user: SessionUser,
    detail: str,
) -> None:
    """Write the stage-3 failure onto the query row.

    update_query_stage swallows its own database errors, so this never masks
    the provider error that brought us here.
    """
    await update_query_stage(
        session,
        req.query_id,
        user.id,
        {"analysis": None, "sources": None, "analysis_error": detail},
    )


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
        result = await run_in_threadpool(
            analyze_trademark,
            mark=req.mark,
            description=req.description,
            nice_class=req.nice_class,
            label=req.label,
            prob_distinctive=req.prob_distinctive,
            attributions=[a.model_dump() for a in req.attributions],
        )
    except openai.APIError as exc:
        # The handler in core/llm_errors.py forms the response, but it never
        # sees the session or the query id. Mark the row failed here, then
        # re-raise so the handler still maps the error the one way it knows.
        # Without this the row keeps its stage-2 shape and the history page
        # shows the check as pending for good.
        await _mark_analysis_failed(session, req, user, llm_error_detail(exc).detail)
        raise
    except RuntimeError as exc:
        # A RuntimeError names an operator problem: a missing provider key, a
        # missing corpus, an empty model reply. The row outlives the request and
        # the history page reads analysis_error back to the user, so store the
        # fixed message and keep the raw text in the log.
        log.error("analyze failed: %s", exc)
        await _mark_analysis_failed(session, req, user, _RUNTIME_FAILURE_DETAIL)
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    await update_query_stage(
        session,
        req.query_id,
        user.id,
        {
            "analysis": result["analysis"],
            "sources": result.get("sources"),
            # A retry that succeeds must clear the marker from the failed run.
            "analysis_error": None,
        },
    )

    return AnalyzeResponse(
        analysis=result["analysis"],
        sources=result.get("sources"),
    )

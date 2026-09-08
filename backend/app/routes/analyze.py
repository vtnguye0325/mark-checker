from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import SessionUser, current_user
from app.db import get_session
from app.limiter import ANALYZE_IP_LIMIT, ANALYZE_USER_LIMIT, _session_key, limiter
from app.query_store import update_query_stage
from app.routes.explain import Attribution
from app.services.llm_service import analyze_trademark
from app.turnstile import verify_turnstile

log = logging.getLogger(__name__)
router = APIRouter()


class AnalyzeRequest(BaseModel):
    mark: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    nice_class: int = Field(..., ge=1, le=45)
    label: str = Field(..., max_length=64)
    prob_distinctive: float = Field(..., ge=0.0, le=1.0)
    attributions: list[Attribution] = Field(..., max_length=16)
    turnstile_token: str = Field("", max_length=2048)
    query_id: str | None = Field(None, max_length=64)


class AnalyzeResponse(BaseModel):
    analysis: str
    sources: dict | None = None


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
        result = analyze_trademark(
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

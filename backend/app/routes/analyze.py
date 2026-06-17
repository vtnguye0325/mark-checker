from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.limiter import ANALYZE_LIMIT, limiter
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


class AnalyzeResponse(BaseModel):
    analysis: str
    sources: dict | None = None


@router.post("/llm-assess", response_model=AnalyzeResponse)
@limiter.limit(ANALYZE_LIMIT)
async def analyze(
    request: Request,  # noqa: ARG001
    req: AnalyzeRequest,
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
    return AnalyzeResponse(
        analysis=result["analysis"],
        sources=result.get("sources"),
    )

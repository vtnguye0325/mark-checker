from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.limiter import ANALYZE_LIMIT, limiter
from app.routes.explain import Attribution
from app.services.llm_service import analyze_trademark

router = APIRouter()


class AnalyzeRequest(BaseModel):
    mark: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    nice_class: int = Field(..., ge=1, le=45)
    label: str = Field(..., max_length=64)
    prob_distinctive: float = Field(..., ge=0.0, le=1.0)
    attributions: list[Attribution] = Field(..., max_length=16)


class AnalyzeResponse(BaseModel):
    analysis: str


@router.post("/analyze", response_model=AnalyzeResponse)
@limiter.limit(ANALYZE_LIMIT)
def analyze(request: Request, req: AnalyzeRequest) -> AnalyzeResponse:  # noqa: ARG001
    try:
        text = analyze_trademark(
            mark=req.mark,
            description=req.description,
            nice_class=req.nice_class,
            label=req.label,
            prob_distinctive=req.prob_distinctive,
            attributions=[a.model_dump() for a in req.attributions],
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return AnalyzeResponse(analysis=text)

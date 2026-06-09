from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.limiter import DEFAULT_LIMIT, limiter
from app.services.model_service import explain_one
from app.services.text_formatter import format_fields

router = APIRouter()


class ExplainRequest(BaseModel):
    mark: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    nice_class: int = Field(..., ge=1, le=45)
    translation: str = Field("", max_length=200)
    pseudo_mark: str = Field("", max_length=200)


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


@router.post("/explain", response_model=ExplainResponse)
@limiter.limit(DEFAULT_LIMIT)
def explain(request: Request, req: ExplainRequest) -> ExplainResponse:  # noqa: ARG001
    fields = format_fields(
        mark=req.mark,
        description=req.description,
        nice_class=req.nice_class,
        translation=req.translation,
        pseudo_mark=req.pseudo_mark,
    )
    result = explain_one(fields)
    return ExplainResponse(**result, formatted_input=". ".join(fields))

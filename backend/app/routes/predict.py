from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.limiter import DEFAULT_LIMIT, limiter
from app.services.model_service import predict_one
from app.services.text_formatter import format_input

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


@router.post("/predict", response_model=PredictResponse)
@limiter.limit(DEFAULT_LIMIT)
def predict(request: Request, req: PredictRequest) -> PredictResponse:  # noqa: ARG001
    text = format_input(
        mark=req.mark,
        description=req.description,
        nice_class=req.nice_class,
        translation=req.translation,
        pseudo_mark=req.pseudo_mark,
    )
    result = predict_one(text)
    return PredictResponse(**result, formatted_input=text)

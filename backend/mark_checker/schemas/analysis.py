"""Request and response models for the three check routes.

The routes share ``Attribution``, so it lives here and has one home.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Attribution(BaseModel):
    field: str = Field(..., max_length=64)
    value: str = Field(..., max_length=2000)
    attribution: float


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


class ExplainRequest(BaseModel):
    mark: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=2000)
    nice_class: int = Field(..., ge=1, le=45)
    translation: str = Field("", max_length=200)
    pseudo_mark: str = Field("", max_length=200)
    query_id: str | None = Field(None, max_length=64)


class ExplainResponse(BaseModel):
    label: str
    prob_distinctive: float
    prob_not_distinctive: float
    formatted_input: str
    attributions: list[Attribution]


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

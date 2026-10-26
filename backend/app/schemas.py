import math
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from .storage import safe_id


class FrameRequest(BaseModel):
    clip_id: str
    time_ms: float = Field(ge=0, allow_inf_nan=False)

    @field_validator('clip_id')
    @classmethod
    def identifier(cls, value):
        return safe_id(value)


class Reference(BaseModel):
    id: str
    evidence_id: str
    crop: list[float] = Field(min_length=4, max_length=4)
    start_clip_id: str
    start_ms: float = Field(ge=0, allow_inf_nan=False)
    confirmed: Literal[True]

    @field_validator('id', 'evidence_id', 'start_clip_id')
    @classmethod
    def identifier(cls, value):
        return safe_id(value)

    @field_validator('crop')
    @classmethod
    def rectangle(cls, value):
        x, y, w, h = value
        if not all(math.isfinite(v) for v in value) or min(x, y) < 0 or min(w, h) <= 0 or x+w > 1.000001 or y+h > 1.000001:
            raise ValueError('Crop must be within normalized image bounds')
        return value


class SequenceRequest(BaseModel):
    clip_ids: list[str] = Field(min_length=1, max_length=3)

    @field_validator('clip_ids')
    @classmethod
    def identifiers(cls, values):
        for value in values:
            safe_id(value)
        if len(set(values)) != len(values):
            raise ValueError('Each clip instance must have a unique ID')
        return values


class AnalysisRequest(SequenceRequest):
    project_id: str
    revision: int = Field(ge=0)
    references: list[Reference] = Field(min_length=1, max_length=100)
    config: dict | None = None

    @field_validator('project_id')
    @classmethod
    def project_identifier(cls, value):
        return safe_id(value)


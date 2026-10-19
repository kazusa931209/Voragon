from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AsrInferenceRequest(BaseModel):
    kind: Literal["partial", "final"]
    segment_id: str = Field(min_length=1)
    language: str = Field(min_length=1)
    audio_base64: str = Field(min_length=1)


class AsrInferenceResponse(BaseModel):
    text: str
    language: str
    confidence: float | None = None

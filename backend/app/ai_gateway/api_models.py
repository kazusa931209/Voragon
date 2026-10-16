from __future__ import annotations

from pydantic import BaseModel, Field


class GatewayAsrInferenceRequest(BaseModel):
    capability: str = Field(min_length=1)
    audio: str = Field(min_length=1, description="Base64-encoded PCM")
    language: str = Field(min_length=1)
    segment_id: str = Field(min_length=1)
    is_final: bool = False


class GatewayAsrInferenceResponse(BaseModel):
    text: str
    segment_id: str
    is_final: bool
    language: str
    confidence: float | None = None
    model: str
    latency_ms: int

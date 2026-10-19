from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.config import Settings


@dataclass(frozen=True)
class TranscriptResult:
    text: str
    language: str
    confidence: float | None = None


@dataclass(frozen=True)
class HealthStatus:
    ready: bool
    backend: str
    model: str | None = None
    message: str | None = None


class ASRError(Exception):
    """Base ASR error."""


class ASRInferenceError(ASRError):
    """Raised when ASR inference fails for a segment."""


class ASRModelUnavailableError(ASRError):
    """Raised when the ASR model is not loaded or unhealthy."""


class ASREngine(Protocol):
    async def transcribe_partial(
        self,
        audio: bytes,
        segment_id: str,
        language: str,
    ) -> TranscriptResult: ...

    async def transcribe_final(
        self,
        audio: bytes,
        segment_id: str,
        language: str,
    ) -> TranscriptResult: ...

    async def health(self) -> HealthStatus: ...

    async def warmup(self) -> None: ...


def create_asr_engine(settings: Settings) -> ASREngine:
    if settings.asr_backend == "faster_whisper":
        from app.asr.faster_whisper import FasterWhisperEngine

        return FasterWhisperEngine(settings)
    if settings.asr_backend == "mock":
        from app.asr.mock_asr import MockASREngine

        return MockASREngine(settings)
    if settings.asr_backend == "remote":
        from app.asr.remote import RemoteASREngine

        return RemoteASREngine(settings)
    raise ValueError(f"Unsupported ASR backend: {settings.asr_backend}")

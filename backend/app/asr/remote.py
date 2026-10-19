from __future__ import annotations

import base64
import logging
from typing import Any, Literal, cast

import httpx

from app.asr.api_models import AsrInferenceRequest, AsrInferenceResponse
from app.asr.base import ASRInferenceError, ASRModelUnavailableError, HealthStatus, TranscriptResult
from app.config import Settings

logger = logging.getLogger(__name__)


class RemoteASREngine:
    """Calls in-cluster asr-service over HTTP (P7-006)."""

    def __init__(
        self,
        settings: Settings,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._settings = settings
        self._backend = settings.asr_backend
        self._model = settings.asr_model
        self._base_url = settings.asr_remote_base_url.rstrip("/")
        self._timeout = httpx.Timeout(settings.asr_remote_timeout_s)
        self._client = client or httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout)
        self._owns_client = client is None
        self._ready = False

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def warmup(self) -> None:
        health = await self.health()
        if not health.ready:
            raise ASRModelUnavailableError(health.message or "Remote ASR service is not ready")
        self._ready = True
        logger.info("Remote ASR ready at %s model=%s", self._base_url, health.model)

    async def health(self) -> HealthStatus:
        try:
            response = await self._client.get("/health")
        except httpx.HTTPError as exc:
            return HealthStatus(
                ready=False,
                backend="remote",
                model=self._model,
                message=f"Remote ASR unreachable: {exc}",
            )

        if response.status_code == 503:
            return HealthStatus(
                ready=False,
                backend="remote",
                model=self._model,
                message="Remote ASR service degraded",
            )

        try:
            response.raise_for_status()
            body: dict[str, Any] = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            return HealthStatus(
                ready=False,
                backend="remote",
                model=self._model,
                message=f"Remote ASR health check failed: {exc}",
            )

        asr = body.get("asr") if isinstance(body.get("asr"), dict) else {}
        remote_ready = bool(asr.get("ready"))
        return HealthStatus(
            ready=remote_ready,
            backend="remote",
            model=asr.get("model") or self._model,
            message=None if remote_ready else "Remote ASR model not ready",
        )

    async def transcribe_partial(
        self,
        audio: bytes,
        segment_id: str,
        language: str,
    ) -> TranscriptResult:
        return await self._transcribe(audio, segment_id, language, kind="partial")

    async def transcribe_final(
        self,
        audio: bytes,
        segment_id: str,
        language: str,
    ) -> TranscriptResult:
        return await self._transcribe(audio, segment_id, language, kind="final")

    async def _transcribe(
        self,
        audio: bytes,
        segment_id: str,
        language: str,
        *,
        kind: str,
    ) -> TranscriptResult:
        if not self._ready:
            raise ASRModelUnavailableError("Remote ASR client is not warmed up")

        payload = AsrInferenceRequest(
            kind=cast(Literal["partial", "final"], kind),
            segment_id=segment_id,
            language=language,
            audio_base64=base64.b64encode(audio).decode("ascii"),
        )

        try:
            response = await self._client.post(
                "/v1/inference/asr",
                json=payload.model_dump(),
            )
        except httpx.HTTPError as exc:
            raise ASRInferenceError(
                f"Remote ASR request failed for segment {segment_id}: {exc}"
            ) from exc

        if response.status_code == 503:
            raise ASRModelUnavailableError("Remote ASR model is not loaded or unhealthy")
        if response.status_code >= 400:
            raise ASRInferenceError(
                f"Remote ASR inference failed for segment {segment_id}: HTTP {response.status_code}"
            )

        try:
            parsed = AsrInferenceResponse.model_validate(response.json())
        except ValueError as exc:
            raise ASRInferenceError(
                f"Remote ASR returned invalid response for segment {segment_id}: {exc}"
            ) from exc

        return TranscriptResult(
            text=parsed.text,
            language=parsed.language,
            confidence=parsed.confidence,
        )

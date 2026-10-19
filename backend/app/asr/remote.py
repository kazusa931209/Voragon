from __future__ import annotations

import base64
import logging
from typing import Any, Literal, cast

import httpx

from app.ai_gateway.api_models import GatewayAsrInferenceResponse
from app.asr.api_models import AsrInferenceRequest, AsrInferenceResponse
from app.asr.base import ASRInferenceError, ASRModelUnavailableError, HealthStatus, TranscriptResult
from app.config import Settings

logger = logging.getLogger(__name__)


class RemoteASREngine:
    """Calls in-cluster asr-service (P7-006) or AI Gateway (P8-006) over HTTP."""

    def __init__(
        self,
        settings: Settings,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._settings = settings
        self._backend = settings.asr_backend
        self._model = settings.asr_model
        self._via_ai_gateway = settings.asr_remote_via_ai_gateway
        self._capability = settings.asr_capability
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
        target = "AI Gateway" if self._via_ai_gateway else "remote ASR"
        logger.info("%s ready at %s model=%s", target, self._base_url, health.model)

    async def health(self) -> HealthStatus:
        backend_label = "remote-ai-gateway" if self._via_ai_gateway else "remote"
        try:
            response = await self._client.get("/health")
        except httpx.HTTPError as exc:
            return HealthStatus(
                ready=False,
                backend=backend_label,
                model=self._capability if self._via_ai_gateway else self._model,
                message=f"Remote ASR unreachable: {exc}",
            )

        if self._via_ai_gateway:
            return self._health_from_ai_gateway(response, backend_label=backend_label)

        if response.status_code == 503:
            return HealthStatus(
                ready=False,
                backend=backend_label,
                model=self._model,
                message="Remote ASR service degraded",
            )

        try:
            response.raise_for_status()
            body: dict[str, Any] = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            return HealthStatus(
                ready=False,
                backend=backend_label,
                model=self._model,
                message=f"Remote ASR health check failed: {exc}",
            )

        asr = body.get("asr") if isinstance(body.get("asr"), dict) else {}
        remote_ready = bool(asr.get("ready"))
        return HealthStatus(
            ready=remote_ready,
            backend=backend_label,
            model=asr.get("model") or self._model,
            message=None if remote_ready else "Remote ASR model not ready",
        )

    def _health_from_ai_gateway(
        self,
        response: httpx.Response,
        *,
        backend_label: str,
    ) -> HealthStatus:
        if response.status_code == 503:
            return HealthStatus(
                ready=False,
                backend=backend_label,
                model=self._capability,
                message="AI Gateway has no routable models",
            )
        try:
            response.raise_for_status()
            body: dict[str, Any] = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            return HealthStatus(
                ready=False,
                backend=backend_label,
                model=self._capability,
                message=f"AI Gateway health check failed: {exc}",
            )

        status = body.get("status")
        routable = body.get("models_routable", True)
        ready = status == "healthy" and bool(routable)
        return HealthStatus(
            ready=ready,
            backend=backend_label,
            model=self._capability,
            message=None if ready else "AI Gateway is degraded or has no routable models",
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

        audio_b64 = base64.b64encode(audio).decode("ascii")
        is_final = kind == "final"

        if self._via_ai_gateway:
            payload = {
                "capability": self._capability,
                "audio": audio_b64,
                "language": language,
                "segment_id": segment_id,
                "is_final": is_final,
            }
        else:
            payload = AsrInferenceRequest(
                kind=cast(Literal["partial", "final"], kind),
                segment_id=segment_id,
                language=language,
                audio_base64=audio_b64,
            ).model_dump()

        try:
            response = await self._client.post(
                "/v1/inference/asr",
                json=payload,
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
            body = response.json()
            if self._via_ai_gateway:
                gateway = GatewayAsrInferenceResponse.model_validate(body)
                return TranscriptResult(
                    text=gateway.text,
                    language=gateway.language,
                    confidence=gateway.confidence,
                )
            asr = AsrInferenceResponse.model_validate(body)
        except ValueError as exc:
            raise ASRInferenceError(
                f"Remote ASR returned invalid response for segment {segment_id}: {exc}"
            ) from exc

        return TranscriptResult(
            text=asr.text,
            language=asr.language,
            confidence=asr.confidence,
        )

from __future__ import annotations

import time

import httpx
from fastapi import HTTPException

from app.ai_gateway.api_models import GatewayAsrInferenceRequest, GatewayAsrInferenceResponse
from app.ai_gateway.health import ModelHealthStore
from app.ai_gateway.registry import ModelRegistry
from app.asr.api_models import AsrInferenceRequest, AsrInferenceResponse


async def proxy_asr_inference(
    registry: ModelRegistry,
    http_client: httpx.AsyncClient,
    body: GatewayAsrInferenceRequest,
    *,
    health_store: ModelHealthStore,
    health_checks_enabled: bool,
) -> GatewayAsrInferenceResponse:
    try:
        model_id, entry = registry.resolve_capability(body.capability)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if entry.type != "asr":
        raise HTTPException(
            status_code=400,
            detail=f"Capability {body.capability!r} resolves to non-ASR model {model_id!r}",
        )

    if not health_store.is_routable(model_id, checks_enabled=health_checks_enabled):
        raise HTTPException(
            status_code=503,
            detail=f"Model {model_id!r} is unhealthy or not yet ready",
        )

    upstream_payload = AsrInferenceRequest(
        kind="final" if body.is_final else "partial",
        segment_id=body.segment_id,
        language=body.language,
        audio_base64=body.audio,
    )
    url = f"{entry.endpoint.rstrip('/')}/v1/inference/asr"
    started = time.perf_counter()

    try:
        response = await http_client.post(url, json=upstream_payload.model_dump())
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Upstream ASR request failed: {exc}",
        ) from exc

    if response.status_code == 503:
        raise HTTPException(status_code=503, detail="Upstream ASR model unavailable")
    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"Upstream ASR inference failed: HTTP {response.status_code}",
        )

    try:
        parsed = AsrInferenceResponse.model_validate(response.json())
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Upstream ASR returned invalid JSON: {exc}",
        ) from exc

    latency_ms = int((time.perf_counter() - started) * 1000)
    return GatewayAsrInferenceResponse(
        text=parsed.text,
        segment_id=body.segment_id,
        is_final=body.is_final,
        language=parsed.language,
        confidence=parsed.confidence,
        model=model_id,
        latency_ms=latency_ms,
    )

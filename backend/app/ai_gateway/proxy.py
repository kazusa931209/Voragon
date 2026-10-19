from __future__ import annotations

import time

import httpx
from fastapi import HTTPException

from app.ai_gateway.api_models import GatewayAsrInferenceRequest, GatewayAsrInferenceResponse
from app.ai_gateway.health import ModelHealthStore
from app.ai_gateway.metrics import record_inference_error, record_inference_success
from app.ai_gateway.registry import ModelRegistry, ModelRegistryEntry
from app.asr.api_models import AsrInferenceRequest, AsrInferenceResponse


async def _forward_asr_to_model(
    http_client: httpx.AsyncClient,
    model_id: str,
    entry: ModelRegistryEntry,
    body: GatewayAsrInferenceRequest,
) -> GatewayAsrInferenceResponse:
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
            detail=f"Upstream ASR request failed for {model_id}: {exc}",
        ) from exc

    if response.status_code == 503:
        raise HTTPException(
            status_code=503,
            detail=f"Upstream ASR model unavailable: {model_id}",
        )
    if response.status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"Upstream ASR inference failed for {model_id}: HTTP {response.status_code}",
        )

    try:
        parsed = AsrInferenceResponse.model_validate(response.json())
    except ValueError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Upstream ASR returned invalid JSON for {model_id}: {exc}",
        ) from exc

    duration_s = time.perf_counter() - started
    latency_ms = int(duration_s * 1000)
    return GatewayAsrInferenceResponse(
        text=parsed.text,
        segment_id=body.segment_id,
        is_final=body.is_final,
        language=parsed.language,
        confidence=parsed.confidence,
        model=model_id,
        latency_ms=latency_ms,
    )


async def proxy_asr_inference(
    registry: ModelRegistry,
    http_client: httpx.AsyncClient,
    body: GatewayAsrInferenceRequest,
    *,
    health_store: ModelHealthStore,
    health_checks_enabled: bool,
) -> GatewayAsrInferenceResponse:
    try:
        chain = registry.routing_chain(body.capability)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    primary_model_id = chain[0][0]
    kind = "final" if body.is_final else "partial"
    tried: list[str] = []
    for model_id, entry in chain:
        if entry.type != "asr":
            record_inference_error(body.capability)
            raise HTTPException(
                status_code=400,
                detail=f"Model {model_id!r} for capability {body.capability!r} is not ASR",
            )
        if not health_store.is_routable(model_id, checks_enabled=health_checks_enabled):
            tried.append(model_id)
            continue
        started = time.perf_counter()
        try:
            result = await _forward_asr_to_model(http_client, model_id, entry, body)
        except HTTPException as exc:
            if exc.status_code == 503:
                tried.append(model_id)
                continue
            record_inference_error(body.capability)
            raise
        duration_s = time.perf_counter() - started
        record_inference_success(
            capability=body.capability,
            model=model_id,
            kind=kind,
            duration_s=duration_s,
            used_fallback=model_id != primary_model_id or bool(tried),
        )
        return result

    if tried:
        record_inference_error(body.capability)
        raise HTTPException(
            status_code=503,
            detail=(
                f"No healthy model available for capability {body.capability!r} "
                f"(tried: {', '.join(tried)})"
            ),
        )
    record_inference_error(body.capability)
    raise HTTPException(status_code=404, detail=f"Unknown capability: {body.capability}")

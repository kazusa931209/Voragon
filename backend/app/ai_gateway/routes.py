from __future__ import annotations

import httpx
from fastapi import APIRouter, Request

from app.ai_gateway.api_models import GatewayAsrInferenceRequest, GatewayAsrInferenceResponse
from app.ai_gateway.health import ModelHealthStore
from app.ai_gateway.proxy import proxy_asr_inference
from app.ai_gateway.registry import ModelRegistry
from app.config import get_settings

router = APIRouter(prefix="/v1", tags=["gateway"])


@router.get("/models")
async def list_models(request: Request) -> dict[str, object]:
    """List registered models and health status (active probes in P8-004)."""
    registry: ModelRegistry = request.app.state.model_registry
    health_store: ModelHealthStore = request.app.state.model_health
    capability_map = registry.capability_map()
    models = []
    for model_id, entry in registry.models.items():
        models.append(
            {
                "id": model_id,
                "type": entry.type,
                "endpoint": entry.endpoint,
                "capabilities": list(entry.capabilities),
                "version": entry.version,
                "languages": list(entry.languages),
                "health_check_interval_s": entry.health_check_interval_s,
                "health": health_store.snapshot(model_id),
            }
        )
    return {"models": models, "capabilities": capability_map}


@router.post("/inference/asr", response_model=GatewayAsrInferenceResponse)
async def inference_asr(
    body: GatewayAsrInferenceRequest,
    request: Request,
) -> GatewayAsrInferenceResponse:
    """Resolve capability and forward to the registered ASR backend."""
    settings = get_settings()
    registry: ModelRegistry = request.app.state.model_registry
    http_client: httpx.AsyncClient = request.app.state.http_client
    health_store: ModelHealthStore = request.app.state.model_health
    return await proxy_asr_inference(
        registry,
        http_client,
        body,
        health_store=health_store,
        health_checks_enabled=settings.ai_gateway_health_checks_enabled,
    )

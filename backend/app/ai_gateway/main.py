"""
Voragon AI Gateway (Phase 8).

Run locally:
    cd backend && pip install -e ".[dev]" && python -m app.ai_gateway.main
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from app.ai_gateway.health import ModelHealthChecker, ModelHealthStore
from app.ai_gateway.metrics import gateway_metrics_body, metrics_content_type
from app.ai_gateway.registry import load_model_registry
from app.ai_gateway.routes import router as gateway_router
from app.config import get_settings
from app.observability.logging_config import configure_logging

SERVICE_NAME = "voragon-ai-gateway"
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    registry_path = Path(settings.ai_gateway_registry_path)
    registry = load_model_registry(registry_path)
    app.state.model_registry = registry
    timeout = httpx.Timeout(settings.ai_gateway_upstream_timeout_s)
    http_client = httpx.AsyncClient(timeout=timeout)
    app.state.http_client = http_client
    health_store = ModelHealthStore(
        failure_threshold=settings.ai_gateway_health_failure_threshold,
        recovery_threshold=settings.ai_gateway_health_recovery_threshold,
    )
    app.state.model_health = health_store
    health_checker = ModelHealthChecker(
        registry,
        http_client,
        health_store,
        check_timeout_s=settings.ai_gateway_health_check_timeout_s,
        check_interval_s=settings.ai_gateway_health_check_interval_s,
        enabled=settings.ai_gateway_health_checks_enabled,
    )
    app.state.health_checker = health_checker
    logger.info(
        "Loaded model registry from %s (%d models)",
        registry_path,
        len(registry.models),
    )
    await health_checker.check_all()
    health_checker.start_background()
    try:
        yield
    finally:
        await health_checker.stop_background()
        await http_client.aclose()


app = FastAPI(title="Voragon AI Gateway", version="0.1.0", lifespan=lifespan)
app.include_router(gateway_router)


@app.get("/health")
async def health(request: Request) -> JSONResponse:
    """Gateway health; 503 when health checks enabled and no model is routable."""
    settings = get_settings()
    registry = request.app.state.model_registry
    health_store: ModelHealthStore = request.app.state.model_health
    model_ids = list(registry.models.keys())
    routable = health_store.any_routable(
        model_ids,
        checks_enabled=settings.ai_gateway_health_checks_enabled,
    )
    ok = routable or not settings.ai_gateway_health_checks_enabled
    payload: dict[str, object] = {
        "status": "healthy" if ok else "degraded",
        "service": SERVICE_NAME,
        "models_routable": routable,
    }
    return JSONResponse(status_code=200 if ok else 503, content=payload)


@app.get("/metrics")
async def metrics(request: Request) -> Response:
    settings = get_settings()
    registry = request.app.state.model_registry
    health_store: ModelHealthStore = request.app.state.model_health
    body = await gateway_metrics_body(
        registry,
        health_store,
        health_checks_enabled=settings.ai_gateway_health_checks_enabled,
    )
    return Response(content=body, media_type=metrics_content_type())


def main() -> None:
    settings = get_settings()
    configure_logging(settings)
    logger.info(
        "Starting AI Gateway on %s:%s", settings.host, settings.ai_gateway_port
    )
    uvicorn.run(
        "app.ai_gateway.main:app",
        host=settings.host,
        port=settings.ai_gateway_port,
        log_level=settings.log_level,
    )


if __name__ == "__main__":
    main()

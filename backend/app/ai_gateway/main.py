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
from fastapi import FastAPI
from fastapi.responses import JSONResponse

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
    logger.info(
        "Loaded model registry from %s (%d models)",
        registry_path,
        len(registry.models),
    )
    try:
        yield
    finally:
        await http_client.aclose()


app = FastAPI(title="Voragon AI Gateway", version="0.1.0", lifespan=lifespan)
app.include_router(gateway_router)


@app.get("/health")
async def health() -> JSONResponse:
    """Kubernetes liveness/readiness baseline (registry probe depth in P8-004)."""
    payload = {
        "status": "healthy",
        "service": SERVICE_NAME,
    }
    return JSONResponse(status_code=200, content=payload)


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

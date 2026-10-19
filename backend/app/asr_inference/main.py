"""
Voragon ASR inference service (P7-003+).

Run locally:
    cd backend && ASR_BACKEND=mock pip install -e ".[dev]" && python -m app.asr_inference.main
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from app.asr.base import ASREngine, create_asr_engine
from app.asr.inference_routes import router as inference_router
from app.config import get_settings
from app.observability.logging_config import configure_logging
from app.observability.metrics import (
    asr_service_metrics_body,
    metrics_content_type,
    observe_model_load_duration,
)

SERVICE_NAME = "voragon-asr-inference"


@asynccontextmanager
async def lifespan(app: FastAPI):
    app_settings = get_settings()
    configure_logging(app_settings)
    logger = logging.getLogger(__name__)
    asr_engine = create_asr_engine(app_settings)
    logger.info(
        "Warming up ASR backend=%s model=%s device=%s",
        app_settings.asr_backend,
        app_settings.asr_model,
        app_settings.asr_device,
    )
    load_started = time.perf_counter()
    await asr_engine.warmup()
    observe_model_load_duration(time.perf_counter() - load_started)
    app.state.asr_engine = asr_engine
    yield


app = FastAPI(title="Voragon ASR Inference", version="0.1.0", lifespan=lifespan)
app.include_router(inference_router)


@app.get("/metrics")
async def metrics() -> Response:
    """Prometheus scrape endpoint (GPU util + ASR inference metrics)."""
    body = await asr_service_metrics_body()
    return Response(content=body, media_type=metrics_content_type())


@app.get("/health")
async def health(request: Request) -> dict[str, object]:
    """Health for Kubernetes probes and operator smoke tests."""
    asr_engine: ASREngine = request.app.state.asr_engine
    asr_health = await asr_engine.health()
    ready = asr_health.ready
    payload: dict[str, object] = {
        "status": "healthy" if ready else "degraded",
        "service": SERVICE_NAME,
        "asr": {
            "ready": ready,
            "backend": asr_health.backend,
            "model": asr_health.model,
            "device": get_settings().asr_device,
        },
    }
    return JSONResponse(status_code=200 if ready else 503, content=payload)


def main() -> None:
    settings = get_settings()
    configure_logging(settings)
    uvicorn.run(
        "app.asr_inference.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
    )


if __name__ == "__main__":
    main()

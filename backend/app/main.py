"""
Voragon realtime backend.

Run locally:
    cd backend
    pip install -e ".[dev]"
    python -m app.main
"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import Response

from app.asr.base import ASREngine, create_asr_engine
from app.observability.metrics import metrics_body, metrics_content_type
from app.config import get_settings
from app.observability.logging_config import configure_logging, log_fields
from app.websocket.connection_registry import shutdown_all
from app.websocket.session_registry import clear_all
from app.websocket.handler import router as websocket_router

settings = get_settings()

configure_logging(settings)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app_settings = get_settings()
    asr_engine = create_asr_engine(app_settings)
    logger.info(
        "Warming up ASR backend=%s model=%s",
        app_settings.asr_backend,
        app_settings.asr_model,
    )
    await asr_engine.warmup()
    app.state.asr_engine = asr_engine
    yield
    if hasattr(asr_engine, "aclose"):
        await asr_engine.aclose()
    log_fields(
        logger,
        logging.INFO,
        "Server shutting down; closing active realtime WebSocket sessions",
        reason="server_shutdown",
    )
    await shutdown_all("server_shutdown")
    await clear_all()


app = FastAPI(title="Voragon Realtime Backend", version="0.1.0", lifespan=lifespan)
app.include_router(websocket_router)


@app.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics scrape endpoint."""
    body = await metrics_body()
    return Response(content=body, media_type=metrics_content_type())


@app.get("/health")
async def health(request: Request) -> dict[str, object]:
    """Health check for load balancers and local development."""
    asr_engine: ASREngine = request.app.state.asr_engine
    asr_health = await asr_engine.health()
    return {
        "status": "healthy" if asr_health.ready else "degraded",
        "service": "voragon-realtime-backend",
        "asr": {
            "ready": asr_health.ready,
            "backend": asr_health.backend,
            "model": asr_health.model,
        },
    }


def main() -> None:
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
    )


if __name__ == "__main__":
    main()

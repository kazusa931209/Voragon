"""
Voragon AI Gateway (Phase 8).

Run locally:
    cd backend && pip install -e ".[dev]" && python -m app.ai_gateway.main
"""

from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.observability.logging_config import configure_logging

SERVICE_NAME = "voragon-ai-gateway"

app = FastAPI(title="Voragon AI Gateway", version="0.1.0")


@app.get("/health")
async def health() -> JSONResponse:
    """Kubernetes liveness/readiness baseline (registry checks in later dev-steps)."""
    payload = {
        "status": "healthy",
        "service": SERVICE_NAME,
    }
    return JSONResponse(status_code=200, content=payload)


def main() -> None:
    settings = get_settings()
    configure_logging(settings)
    logging.getLogger(__name__).info(
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

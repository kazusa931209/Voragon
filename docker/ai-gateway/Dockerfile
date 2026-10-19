# Build context: repository root (see docker/ai-gateway/README.md).
FROM python:3.11-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/app ./app

# Gateway image: HTTP routing only (slim deps; no full backend package install).
RUN pip install --no-cache-dir \
    "fastapi>=0.115.0" \
    "httpx>=0.28.0" \
    "pydantic-settings>=2.6.0" \
    "pyyaml>=6.0.0" \
    "uvicorn[standard]>=0.32.0"

ENV HOST=0.0.0.0
ENV AI_GATEWAY_PORT=8080
ENV LOG_FORMAT=json

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -fsS http://127.0.0.1:8080/health || exit 1

CMD ["python", "-m", "app.ai_gateway.main"]

# Voragon Backend

Python FastAPI realtime backend for Voragon.

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env   # optional; edit ASR_MODEL, VAD_BACKEND, etc.
```

## Run

```bash
cd backend
python -m app.main
```

Faster local ASR (smaller model):

```bash
ASR_MODEL=tiny python -m app.main
```

Startup logs show the resolved model, e.g. `Warming up ASR backend=faster_whisper model=tiny`.

Server listens on `http://0.0.0.0:8000` by default.

### Configuration

See [`.env.example`](.env.example) for all settings. Common overrides:

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Bind address |
| `PORT` | `8000` | Bind port |
| `LOG_LEVEL` | `info` | Logging level |
| `LOG_FORMAT` | `console` | `console` or `json` (structured JSON to stdout) |
| `ASR_BACKEND` | `faster_whisper` | ASR adapter (`faster_whisper`, `mock`, `remote`) |
| `ASR_REMOTE_BASE_URL` | `http://asr-service:8081` | Remote HTTP base when `ASR_BACKEND=remote` (EKS: `http://ai-gateway:8080`) |
| `ASR_REMOTE_VIA_AI_GATEWAY` | `false` | Gateway inference API (`ASR_CAPABILITY`, default `asr.default`) |
| `ASR_CAPABILITY` | `asr.default` | Capability alias when routing via AI Gateway |
| `ASR_MODEL` | `large-v3-turbo` | Whisper model id (e.g. `tiny`, `base`, `large-v3-turbo`) |

## Health Check

```bash
curl http://localhost:8000/health
```

## Metrics

```bash
curl http://localhost:8000/metrics
```

Prometheus text format; see [Observability](../docs/operations/observability.md).

## Logging

```bash
LOG_FORMAT=json python -m app.main
```

See [Local Development](../docs/operations/local-development.md#logging).

## WebSocket

Connect to `ws://localhost:8000/v1/realtime`. The server sends `session.started` immediately after the connection is accepted.

## Tests

```bash
pytest
```

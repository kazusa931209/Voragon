import asyncio
import base64
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from httpx import ASGITransport
from pydantic import ValidationError

from app.ai_gateway.health import ModelHealthStore
from app.ai_gateway.registry import load_model_registry
from app.asr.api_models import AsrInferenceRequest, AsrInferenceResponse
from app.asr.mock_asr import MIN_AUDIO_BYTES_FOR_TEXT, MockASREngine
from app.config import Settings


def _registry_with_fallback(path: Path) -> None:
    path.write_text(
        """
models:
  primary-model:
    type: asr
    endpoint: http://asr-primary:8081
    capabilities: [asr.default]
    version: "1"
  fallback-model:
    type: asr
    endpoint: http://asr-fallback:8081
    capabilities: []
    version: "1"
routing:
  asr.default:
    primary: primary-model
    fallback: [fallback-model]
""".strip(),
        encoding="utf-8",
    )


def _dual_backend_mock_app(*, primary_warmed: bool, fallback_warmed: bool) -> FastAPI:
    primary = MockASREngine(Settings(asr_backend="mock", asr_model="tiny"))
    fallback = MockASREngine(Settings(asr_backend="mock", asr_model="tiny"))
    if primary_warmed:
        asyncio.run(primary.warmup())
    if fallback_warmed:
        asyncio.run(fallback.warmup())

    app = FastAPI()

    def _pick_engine(request: Request) -> MockASREngine:
        host = request.url.hostname or request.headers.get("host", "").split(":")[0]
        if host == "asr-primary":
            return primary
        if host == "asr-fallback":
            return fallback
        raise RuntimeError(f"unexpected host: {host}")

    @app.get("/health")
    async def health(request: Request) -> dict[str, object]:
        engine = _pick_engine(request)
        h = await engine.health()
        return {
            "status": "healthy" if h.ready else "degraded",
            "asr": {"ready": h.ready, "backend": h.backend, "model": h.model},
        }

    @app.post("/v1/inference/asr", response_model=AsrInferenceResponse)
    async def infer(request: Request, body: AsrInferenceRequest) -> AsrInferenceResponse:
        engine = _pick_engine(request)
        audio = base64.b64decode(body.audio_base64)
        if body.kind == "partial":
            result = await engine.transcribe_partial(audio, body.segment_id, body.language)
        else:
            result = await engine.transcribe_final(audio, body.segment_id, body.language)
        return AsrInferenceResponse(
            text=result.text,
            language=result.language,
            confidence=result.confidence,
        )

    return app


@pytest.fixture
def fallback_gateway(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> TestClient:
    registry_path = tmp_path / "registry.yaml"
    _registry_with_fallback(registry_path)
    monkeypatch.setenv("AI_GATEWAY_REGISTRY_PATH", str(registry_path))
    monkeypatch.setenv("AI_GATEWAY_HEALTH_CHECKS_ENABLED", "true")
    monkeypatch.setenv("AI_GATEWAY_HEALTH_CHECK_INTERVAL_S", "86400")

    import importlib

    import app.ai_gateway.main as gateway_main

    importlib.reload(gateway_main)

    mock_app = _dual_backend_mock_app(primary_warmed=True, fallback_warmed=True)
    transport = ASGITransport(app=mock_app)
    http_client = httpx.AsyncClient(transport=transport, timeout=30.0)

    with TestClient(gateway_main.app) as client:
        checker = client.app.state.health_checker
        if checker._task is not None:
            checker._task.cancel()
            checker._task = None
        client.app.state.http_client = http_client
        existing = client.app.state.model_health
        store = ModelHealthStore(
            failure_threshold=existing.failure_threshold,
            recovery_threshold=existing.recovery_threshold,
        )
        client.app.state.model_health = store
        store.record_probe("primary-model", success=False, message="down")
        store.record_probe("primary-model", success=False, message="down")
        store.record_probe("primary-model", success=False, message="down")
        store.record_probe("fallback-model", success=True, message=None)
        yield client
    asyncio.run(http_client.aclose())


def test_inference_uses_fallback_when_primary_unhealthy(
    fallback_gateway: TestClient,
) -> None:
    audio_b64 = base64.b64encode(b"\x00" * MIN_AUDIO_BYTES_FOR_TEXT).decode("ascii")
    response = fallback_gateway.post(
        "/v1/inference/asr",
        json={
            "capability": "asr.default",
            "audio": audio_b64,
            "language": "en",
            "segment_id": "seg-fb",
            "is_final": False,
        },
    )
    assert response.status_code == 200
    assert response.json()["model"] == "fallback-model"
    assert response.json()["text"] == "partial-seg-fb"


def test_inference_503_when_all_models_unhealthy(fallback_gateway: TestClient) -> None:
    store: ModelHealthStore = fallback_gateway.app.state.model_health
    store.record_probe("fallback-model", success=False, message="down")
    store.record_probe("fallback-model", success=False, message="down")
    store.record_probe("fallback-model", success=False, message="down")

    audio_b64 = base64.b64encode(b"\x00" * MIN_AUDIO_BYTES_FOR_TEXT).decode("ascii")
    response = fallback_gateway.post(
        "/v1/inference/asr",
        json={
            "capability": "asr.default",
            "audio": audio_b64,
            "language": "en",
            "segment_id": "seg-none",
            "is_final": True,
        },
    )
    assert response.status_code == 503


def test_invalid_routing_reference_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad-routing.yaml"
    path.write_text(
        """
models:
  primary-model:
    type: asr
    endpoint: http://localhost:1
    capabilities: [asr.default]
    version: "1"
routing:
  asr.default:
    primary: primary-model
    fallback: [missing-model]
""".strip(),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError, match="missing-model"):
        load_model_registry(path)

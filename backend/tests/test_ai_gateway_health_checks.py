import asyncio
import base64

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport

from app.ai_gateway.health import ModelHealthStore, probe_asr_backend
from app.ai_gateway.registry import ModelRegistry, ModelRegistryEntry
from app.asr.inference_routes import router as inference_router
from app.asr.mock_asr import MIN_AUDIO_BYTES_FOR_TEXT, MockASREngine
from app.config import Settings


def test_health_store_failure_and_recovery_thresholds() -> None:
    store = ModelHealthStore(failure_threshold=3, recovery_threshold=2)
    model_id = "m1"

    store.record_probe(model_id, success=False, message="fail")
    assert store.is_routable(model_id, checks_enabled=True) is False
    store.record_probe(model_id, success=False, message="fail")
    store.record_probe(model_id, success=False, message="fail")
    assert store.snapshot(model_id)["status"] == "unhealthy"

    store.record_probe(model_id, success=True, message=None)
    assert store.is_routable(model_id, checks_enabled=True) is False
    store.record_probe(model_id, success=True, message=None)
    assert store.is_routable(model_id, checks_enabled=True) is True
    assert store.snapshot(model_id)["status"] == "healthy"


def test_health_store_cold_start_single_success() -> None:
    store = ModelHealthStore(failure_threshold=3, recovery_threshold=2)
    store.record_probe("m1", success=True, message=None)
    assert store.is_routable("m1", checks_enabled=True) is True


@pytest.mark.asyncio
async def test_probe_asr_backend_reads_asr_ready() -> None:
    engine = MockASREngine(Settings(asr_backend="mock", asr_model="tiny"))
    app = FastAPI()
    app.state.asr_engine = engine
    app.include_router(inference_router)
    await engine.warmup()

    @app.get("/health")
    async def health() -> dict[str, object]:
        h = await engine.health()
        return {"asr": {"ready": h.ready, "backend": h.backend, "model": h.model}}

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://asr.test") as client:
        entry = ModelRegistryEntry(
            type="asr",
            endpoint="http://asr.test",
            capabilities=["asr.default"],
            version="1",
        )
        ok, msg = await probe_asr_backend(client, entry, timeout_s=5.0)
    assert ok is True
    assert msg is None


def _mock_asr_app(*, warmed: bool) -> FastAPI:
    engine = MockASREngine(Settings(asr_backend="mock", asr_model="tiny"))
    app = FastAPI()
    app.state.asr_engine = engine
    app.include_router(inference_router)

    @app.get("/health")
    async def health() -> dict[str, object]:
        h = await engine.health()
        return {
            "status": "healthy" if h.ready else "degraded",
            "asr": {"ready": h.ready, "backend": h.backend, "model": h.model},
        }

    if warmed:
        asyncio.run(engine.warmup())
    return app


@pytest.fixture
def gateway_with_mock_asr(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("AI_GATEWAY_HEALTH_CHECKS_ENABLED", "true")
    monkeypatch.setenv("AI_GATEWAY_HEALTH_CHECK_INTERVAL_S", "86400")
    import importlib

    import app.ai_gateway.main as gateway_main

    importlib.reload(gateway_main)
    mock_asr = _mock_asr_app(warmed=True)
    transport = ASGITransport(app=mock_asr)
    http_client = httpx.AsyncClient(
        transport=transport,
        base_url="http://asr-service:8081",
        timeout=30.0,
    )
    with TestClient(gateway_main.app) as client:
        checker = client.app.state.health_checker
        if checker._task is not None:
            checker._task.cancel()
            checker._task = None
        client.app.state.http_client = http_client
        store = ModelHealthStore(
            failure_threshold=client.app.state.model_health.failure_threshold,
            recovery_threshold=client.app.state.model_health.recovery_threshold,
        )
        client.app.state.model_health = store
        store.record_probe("whisper-large-v3-turbo", success=True, message=None)
        yield client
    asyncio.run(http_client.aclose())


def test_models_show_healthy_with_mock_backend(gateway_with_mock_asr: TestClient) -> None:
    response = gateway_with_mock_asr.get("/v1/models")
    assert response.status_code == 200
    health = response.json()["models"][0]["health"]
    assert health["status"] == "healthy"
    assert health["ready"] is True


def test_gateway_health_ok_when_model_healthy(gateway_with_mock_asr: TestClient) -> None:
    response = gateway_with_mock_asr.get("/health")
    assert response.status_code == 200
    assert response.json()["models_routable"] is True


def test_inference_blocked_when_model_unhealthy(gateway_with_mock_asr: TestClient) -> None:
    store = gateway_with_mock_asr.app.state.model_health
    store.record_probe("whisper-large-v3-turbo", success=False, message="down")
    store.record_probe("whisper-large-v3-turbo", success=False, message="down")
    store.record_probe("whisper-large-v3-turbo", success=False, message="down")

    audio_b64 = base64.b64encode(b"\x00" * MIN_AUDIO_BYTES_FOR_TEXT).decode("ascii")
    response = gateway_with_mock_asr.post(
        "/v1/inference/asr",
        json={
            "capability": "asr.default",
            "audio": audio_b64,
            "language": "en",
            "segment_id": "seg-blocked",
            "is_final": False,
        },
    )
    assert response.status_code == 503

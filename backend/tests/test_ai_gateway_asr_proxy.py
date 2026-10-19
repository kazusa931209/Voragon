import asyncio
import base64

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport

from app.asr.inference_routes import router as inference_router
from app.asr.mock_asr import MIN_AUDIO_BYTES_FOR_TEXT, MockASREngine
from app.config import Settings


def _mock_asr_app(*, warmed: bool) -> FastAPI:
    engine = MockASREngine(Settings(asr_backend="mock", asr_model="tiny"))
    app = FastAPI()
    app.state.asr_engine = engine
    app.include_router(inference_router)
    if warmed:
        asyncio.run(engine.warmup())
    return app


@pytest.fixture
def gateway_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("AI_GATEWAY_HEALTH_CHECKS_ENABLED", "false")
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
        client.app.state.http_client = http_client
        yield client
    asyncio.run(http_client.aclose())


def test_gateway_proxies_asr_inference(gateway_client: TestClient) -> None:
    audio_b64 = base64.b64encode(b"\x00" * MIN_AUDIO_BYTES_FOR_TEXT).decode("ascii")
    payload = {
        "capability": "asr.default",
        "audio": audio_b64,
        "language": "en",
        "segment_id": "seg-gw-1",
        "is_final": False,
    }
    response = gateway_client.post("/v1/inference/asr", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "partial-seg-gw-1"
    assert body["model"] == "whisper-large-v3-turbo"
    assert body["segment_id"] == "seg-gw-1"
    assert body["is_final"] is False
    assert body["latency_ms"] >= 0


def test_gateway_unknown_capability(gateway_client: TestClient) -> None:
    response = gateway_client.post(
        "/v1/inference/asr",
        json={
            "capability": "asr.unknown",
            "audio": "YQ==",
            "language": "en",
            "segment_id": "seg-x",
            "is_final": True,
        },
    )
    assert response.status_code == 404


def test_gateway_upstream_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_GATEWAY_HEALTH_CHECKS_ENABLED", "false")
    import importlib

    import app.ai_gateway.main as gateway_main

    importlib.reload(gateway_main)
    mock_asr = _mock_asr_app(warmed=False)
    transport = ASGITransport(app=mock_asr)
    http_client = httpx.AsyncClient(
        transport=transport,
        base_url="http://asr-service:8081",
        timeout=30.0,
    )
    audio_b64 = base64.b64encode(b"\x00" * MIN_AUDIO_BYTES_FOR_TEXT).decode("ascii")
    with TestClient(gateway_main.app) as client:
        client.app.state.http_client = http_client
        response = client.post(
            "/v1/inference/asr",
            json={
                "capability": "asr.default",
                "audio": audio_b64,
                "language": "en",
                "segment_id": "seg-down",
                "is_final": False,
            },
        )
    asyncio.run(http_client.aclose())
    assert response.status_code == 503

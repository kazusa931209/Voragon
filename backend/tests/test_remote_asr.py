import base64

import httpx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.asr.base import ASRInferenceError, ASRModelUnavailableError, create_asr_engine
from app.asr.inference_routes import router as inference_router
from app.asr.mock_asr import MIN_AUDIO_BYTES_FOR_TEXT, MockASREngine
from app.asr.remote import RemoteASREngine
from app.config import Settings


def _build_mock_asr_service() -> tuple[FastAPI, MockASREngine]:
    engine = MockASREngine(Settings(asr_backend="mock", asr_model="tiny"))
    app = FastAPI()
    app.include_router(inference_router)

    @app.get("/health")
    async def health() -> dict[str, object]:
        health_status = await engine.health()
        return {
            "status": "healthy" if health_status.ready else "degraded",
            "asr": {
                "ready": health_status.ready,
                "backend": health_status.backend,
                "model": health_status.model,
            },
        }

    return app, engine


async def _prepare_mock_asr_service(*, warmed: bool) -> FastAPI:
    app, engine = _build_mock_asr_service()
    app.state.asr_engine = engine
    if warmed:
        await engine.warmup()
    return app


@pytest.fixture
def remote_settings() -> Settings:
    return Settings(
        asr_backend="remote",
        asr_model="tiny",
        asr_remote_base_url="http://asr.test",
    )


async def test_create_asr_engine_selects_remote(remote_settings: Settings) -> None:
    engine = create_asr_engine(remote_settings)
    assert engine.__class__.__name__ == "RemoteASREngine"


async def test_remote_asr_end_to_end_with_mock_service(remote_settings: Settings) -> None:
    mock_app = await _prepare_mock_asr_service(warmed=True)
    transport = ASGITransport(app=mock_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://asr.test") as client:
        engine = RemoteASREngine(remote_settings, client=client)
        await engine.warmup()
        audio = b"\x00" * MIN_AUDIO_BYTES_FOR_TEXT

        partial = await engine.transcribe_partial(audio, "seg-remote", "en")
        final = await engine.transcribe_final(audio, "seg-remote", "en")

    assert partial.text == "partial-seg-remote"
    assert final.text == "final-seg-remote"


async def test_remote_asr_unavailable_when_health_503(remote_settings: Settings) -> None:
    mock_app = await _prepare_mock_asr_service(warmed=False)
    transport = ASGITransport(app=mock_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://asr.test") as client:
        engine = RemoteASREngine(remote_settings, client=client)
        with pytest.raises(ASRModelUnavailableError):
            await engine.warmup()


async def test_remote_asr_inference_error_on_http_502(remote_settings: Settings) -> None:
    app = FastAPI()

    @app.get("/health")
    async def health() -> dict[str, object]:
        return {"status": "healthy", "asr": {"ready": True, "model": "tiny"}}

    @app.post("/v1/inference/asr")
    async def fail() -> None:
        from fastapi import HTTPException

        raise HTTPException(status_code=502, detail="gpu oom")

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://asr.test") as client:
        engine = RemoteASREngine(remote_settings, client=client)
        await engine.warmup()
        with pytest.raises(ASRInferenceError):
            await engine.transcribe_final(b"\x00" * MIN_AUDIO_BYTES_FOR_TEXT, "seg", "en")


def _build_mock_ai_gateway() -> FastAPI:
    app = FastAPI()

    @app.get("/health")
    async def health() -> dict[str, object]:
        return {"status": "healthy", "service": "voragon-ai-gateway", "models_routable": True}

    @app.post("/v1/inference/asr")
    async def infer(payload: dict[str, object]) -> dict[str, object]:
        segment_id = str(payload.get("segment_id", ""))
        is_final = bool(payload.get("is_final"))
        assert payload.get("capability") == "asr.default"
        assert "audio" in payload
        kind = "final" if is_final else "partial"
        return {
            "text": f"{kind}-{segment_id}",
            "segment_id": segment_id,
            "is_final": is_final,
            "language": payload.get("language", "en"),
            "confidence": 0.9,
            "model": "whisper-large-v3-turbo",
            "latency_ms": 12,
        }

    return app


async def test_remote_asr_via_ai_gateway_end_to_end() -> None:
    settings = Settings(
        asr_backend="remote",
        asr_model="large-v3-turbo",
        asr_remote_base_url="http://ai-gateway.test",
        asr_remote_via_ai_gateway=True,
        asr_capability="asr.default",
    )
    mock_app = _build_mock_ai_gateway()
    transport = ASGITransport(app=mock_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://ai-gateway.test") as client:
        engine = RemoteASREngine(settings, client=client)
        await engine.warmup()
        health = await engine.health()
        assert health.backend == "remote-ai-gateway"
        assert health.ready is True

        audio = b"\x00" * MIN_AUDIO_BYTES_FOR_TEXT
        partial = await engine.transcribe_partial(audio, "seg-gw", "en")
        final = await engine.transcribe_final(audio, "seg-gw", "en")

    assert partial.text == "partial-seg-gw"
    assert final.text == "final-seg-gw"


async def test_remote_asr_via_ai_gateway_unhealthy_on_503() -> None:
    settings = Settings(
        asr_backend="remote",
        asr_remote_base_url="http://ai-gateway.test",
        asr_remote_via_ai_gateway=True,
    )
    app = FastAPI()

    @app.get("/health")
    async def health() -> None:
        from fastapi import Response

        return Response(
            status_code=503,
            content='{"status":"degraded","models_routable":false}',
            media_type="application/json",
        )

    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://ai-gateway.test") as client:
        engine = RemoteASREngine(settings, client=client)
        with pytest.raises(ASRModelUnavailableError):
            await engine.warmup()


async def test_asr_inference_http_route_with_test_client() -> None:
    from fastapi.testclient import TestClient

    mock_app = await _prepare_mock_asr_service(warmed=True)
    audio_b64 = base64.b64encode(b"\x00" * MIN_AUDIO_BYTES_FOR_TEXT).decode("ascii")

    with TestClient(mock_app) as client:
        response = client.post(
            "/v1/inference/asr",
            json={
                "kind": "final",
                "segment_id": "seg-http",
                "language": "en",
                "audio_base64": audio_b64,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["text"] == "final-seg-http"
    assert body["language"] == "en"

import importlib
import re

import pytest
from fastapi.testclient import TestClient


def _counter_value(body: str, name: str, labels: str) -> float:
    pattern = rf"^{re.escape(name)}\{{{labels}\}} (\d+(?:\.\d+)?(?:e[+-]?\d+)?)$"
    for line in body.splitlines():
        match = re.match(pattern, line)
        if match:
            return float(match.group(1))
    raise AssertionError(f"Counter {name}{{{labels}}} not found in metrics body")


@pytest.fixture
def ai_gateway_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("AI_GATEWAY_HEALTH_CHECKS_ENABLED", "false")
    import app.ai_gateway.main as gateway_main

    importlib.reload(gateway_main)
    with TestClient(gateway_main.app) as client:
        yield client


def test_ai_gateway_metrics_endpoint(ai_gateway_client: TestClient) -> None:
    response = ai_gateway_client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    body = response.text
    assert "# HELP voragon_gateway_inference_requests_total" in body
    assert "# HELP voragon_gateway_models_routable" in body
    assert "# TYPE voragon_gateway_models_routable gauge" in body


def test_ai_gateway_inference_increments_request_counter(
    ai_gateway_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import httpx

    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/inference/asr":
            return httpx.Response(
                200,
                json={
                    "text": "ok",
                    "language": "en",
                    "confidence": 0.9,
                },
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    http_client = httpx.AsyncClient(transport=transport)
    monkeypatch.setattr(
        ai_gateway_client.app.state,
        "http_client",
        http_client,
    )

    baseline = ai_gateway_client.get("/metrics").text
    try:
        before = _counter_value(
            baseline,
            "voragon_gateway_inference_requests_total",
            'capability="asr.default",kind="final",model="whisper-large-v3-turbo"',
        )
    except AssertionError:
        before = 0.0

    response = ai_gateway_client.post(
        "/v1/inference/asr",
        json={
            "capability": "asr.default",
            "audio": "AA==",
            "language": "en",
            "segment_id": "seg-metrics",
            "is_final": True,
        },
    )
    assert response.status_code == 200

    after = _counter_value(
        ai_gateway_client.get("/metrics").text,
        "voragon_gateway_inference_requests_total",
        'capability="asr.default",kind="final",model="whisper-large-v3-turbo"',
    )
    assert after == before + 1

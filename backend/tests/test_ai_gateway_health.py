import importlib

import pytest
from fastapi.testclient import TestClient


def test_ai_gateway_health(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_GATEWAY_HEALTH_CHECKS_ENABLED", "false")
    import app.ai_gateway.main as gateway_main

    importlib.reload(gateway_main)
    with TestClient(gateway_main.app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["service"] == "voragon-ai-gateway"

import importlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.ai_gateway.registry import load_model_registry


def test_load_default_registry() -> None:
    registry = load_model_registry()
    model_id, entry = registry.resolve_capability("asr.default")
    assert model_id == "whisper-large-v3-turbo"
    assert entry.endpoint == "http://asr-service:8081"
    assert entry.type == "asr"


def test_duplicate_capability_rejected(tmp_path: Path) -> None:
    path = tmp_path / "bad.yaml"
    path.write_text(
        """
models:
  a:
    type: asr
    endpoint: http://localhost:1
    capabilities: [asr.default]
    version: "1"
  b:
    type: asr
    endpoint: http://localhost:2
    capabilities: [asr.default]
    version: "1"
""".strip(),
        encoding="utf-8",
    )
    with pytest.raises(ValidationError, match="asr.default"):
        load_model_registry(path)


@pytest.fixture
def ai_gateway_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("AI_GATEWAY_HEALTH_CHECKS_ENABLED", "false")
    import importlib

    import app.ai_gateway.main as gateway_main

    importlib.reload(gateway_main)
    with TestClient(gateway_main.app) as client:
        yield client


def test_list_models_endpoint(ai_gateway_client: TestClient) -> None:
    response = ai_gateway_client.get("/v1/models")
    assert response.status_code == 200
    body = response.json()
    assert body["capabilities"]["asr.default"] == "whisper-large-v3-turbo"
    assert len(body["models"]) == 1
    model = body["models"][0]
    assert model["id"] == "whisper-large-v3-turbo"
    assert model["health"]["status"] == "unchecked"


def test_custom_registry_path(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    path = tmp_path / "custom.yaml"
    path.write_text(
        """
models:
  custom-asr:
    type: asr
    endpoint: http://127.0.0.1:9999
    capabilities: [asr.default]
    version: "9"
    languages: [en]
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("AI_GATEWAY_REGISTRY_PATH", str(path))
    monkeypatch.setenv("AI_GATEWAY_HEALTH_CHECKS_ENABLED", "false")
    import app.ai_gateway.main as gateway_main

    importlib.reload(gateway_main)
    with TestClient(gateway_main.app) as client:
        response = client.get("/v1/models")
    assert response.status_code == 200
    assert response.json()["models"][0]["id"] == "custom-asr"

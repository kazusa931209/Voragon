import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def asr_inference_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("ASR_BACKEND", "mock")
    from app.asr_inference.main import app

    with TestClient(app) as client:
        yield client


def test_asr_inference_health_mock(asr_inference_client: TestClient) -> None:
    response = asr_inference_client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "voragon-asr-inference"
    assert body["status"] == "healthy"
    assert body["asr"]["ready"] is True
    assert body["asr"]["backend"] == "mock"


def test_asr_inference_dockerfile_contract() -> None:
    from pathlib import Path

    dockerfile = Path(__file__).resolve().parents[2] / "docker" / "asr-inference" / "Dockerfile"
    text = dockerfile.read_text(encoding="utf-8")
    assert "nvidia/cuda" in text
    assert "app.asr_inference.main" in text
    assert "ASR_DEVICE=cuda" in text

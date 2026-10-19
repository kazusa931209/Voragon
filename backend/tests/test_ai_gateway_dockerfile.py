from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_DOCKERFILE = _REPO / "docker" / "ai-gateway" / "Dockerfile"


def test_ai_gateway_dockerfile_contract() -> None:
    text = _DOCKERFILE.read_text(encoding="utf-8")
    assert "python:3.11-slim" in text
    assert "app.ai_gateway.main" in text
    assert "AI_GATEWAY_PORT=8080" in text
    assert "fastapi>=" in text
    assert "faster-whisper>=" not in text
    assert "torch>=" not in text

from fastapi.testclient import TestClient


def test_ai_gateway_health() -> None:
    from app.ai_gateway.main import app

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["service"] == "voragon-ai-gateway"

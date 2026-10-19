import time

import jwt
import pytest
from fastapi.testclient import TestClient

from app.auth.jwt import REALTIME_JWT_AUDIENCE
from app.main import app


def _mint_token(secret: str, *, sub: str = "staging-client", exp_offset: int = 3600) -> str:
    now = int(time.time())
    payload = {
        "sub": sub,
        "aud": REALTIME_JWT_AUDIENCE,
        "iat": now,
        "exp": now + exp_offset,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def test_websocket_auth_disabled_by_default() -> None:
    with TestClient(app) as client:
        with client.websocket_connect("/v1/realtime") as websocket:
            message = websocket.receive_json()
    assert message["type"] == "session.started"


def test_websocket_rejects_missing_token_when_auth_required(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("JWT_AUTH_REQUIRED", "true")
    monkeypatch.setenv("JWT_SECRET", "test-secret-at-least-32-bytes-long!!")
    with TestClient(app) as client:
        with pytest.raises(Exception):
            with client.websocket_connect("/v1/realtime"):
                pass


def test_websocket_accepts_bearer_token(monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "test-secret-at-least-32-bytes-long!!"
    monkeypatch.setenv("JWT_AUTH_REQUIRED", "true")
    monkeypatch.setenv("JWT_SECRET", secret)
    token = _mint_token(secret)
    with TestClient(app) as client:
        with client.websocket_connect(
            "/v1/realtime",
            headers={"Authorization": f"Bearer {token}"},
        ) as websocket:
            message = websocket.receive_json()
    assert message["type"] == "session.started"


def test_websocket_accepts_access_token_query(monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "test-secret-at-least-32-bytes-long!!"
    monkeypatch.setenv("JWT_AUTH_REQUIRED", "true")
    monkeypatch.setenv("JWT_SECRET", secret)
    token = _mint_token(secret)
    with TestClient(app) as client:
        with client.websocket_connect(f"/v1/realtime?access_token={token}") as websocket:
            message = websocket.receive_json()
    assert message["type"] == "session.started"


def test_websocket_rejects_expired_token(monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "test-secret-at-least-32-bytes-long!!"
    monkeypatch.setenv("JWT_AUTH_REQUIRED", "true")
    monkeypatch.setenv("JWT_SECRET", secret)
    token = _mint_token(secret, exp_offset=-10)
    with TestClient(app) as client:
        with pytest.raises(Exception):
            with client.websocket_connect(
                "/v1/realtime",
                headers={"Authorization": f"Bearer {token}"},
            ):
                pass

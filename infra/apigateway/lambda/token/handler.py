"""Mint HS256 JWTs for staging WebSocket clients (API Gateway HTTP POST /v1/auth/token)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

AUDIENCE = "voragon-realtime"
TOKEN_TTL_S = 3600


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _sign_hs256(payload: dict[str, Any], secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64url(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    return f"{header_b64}.{payload_b64}.{_b64url(signature)}"


def _response(status: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body),
    }


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    expected_key = os.environ.get("MINT_API_KEY", "")
    headers = {k.lower(): v for k, v in (event.get("headers") or {}).items()}
    provided = headers.get("x-api-key", "")
    if not expected_key or provided != expected_key:
        return _response(401, {"error": "unauthorized", "message": "Invalid or missing x-api-key"})

    secret = os.environ["JWT_SECRET"]
    now = int(time.time())
    token = _sign_hs256(
        {
            "sub": "voragon-staging",
            "aud": AUDIENCE,
            "iat": now,
            "exp": now + TOKEN_TTL_S,
        },
        secret,
    )
    return _response(
        200,
        {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": TOKEN_TTL_S,
        },
    )

"""HS256 JWT helpers for production WebSocket authentication."""

from __future__ import annotations

import logging
from typing import Any

import jwt
from fastapi import WebSocket

logger = logging.getLogger(__name__)

REALTIME_JWT_AUDIENCE = "voragon-realtime"


class JwtAuthError(Exception):
    """Token missing, malformed, or invalid."""


def extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    return token or None


def extract_access_token_from_websocket(websocket: WebSocket) -> str | None:
    header = websocket.headers.get("authorization")
    token = extract_bearer_token(header)
    if token:
        return token
    query = websocket.query_params.get("access_token")
    if query and query.strip():
        return query.strip()
    return None


def verify_realtime_jwt(
    token: str,
    *,
    secret: str,
    audience: str = REALTIME_JWT_AUDIENCE,
) -> dict[str, Any]:
    try:
        return jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            audience=audience,
            options={"require": ["exp", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise JwtAuthError(str(exc)) from exc


async def require_realtime_jwt(
    websocket: WebSocket,
    *,
    secret: str,
    audience: str = REALTIME_JWT_AUDIENCE,
) -> dict[str, Any]:
    token = extract_access_token_from_websocket(websocket)
    if not token:
        raise JwtAuthError("missing token")
    return verify_realtime_jwt(token, secret=secret, audience=audience)

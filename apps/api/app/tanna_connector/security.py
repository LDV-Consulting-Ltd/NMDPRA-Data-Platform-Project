"""Bearer token authentication for Tanna connector endpoints."""
from __future__ import annotations

import os

from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.tanna_connector.config import get_tanna_config

_bearer = HTTPBearer(auto_error=False)


def _expected_token() -> str:
    config = get_tanna_config()
    if config.normalized_token:
        return config.normalized_token
    return os.getenv("TANNA_CONNECTOR_TOKEN", "").strip()


def require_tanna_token(
    credentials: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> bool:
    """
    Validate Authorization: Bearer <TANNA_CONNECTOR_TOKEN>.
    Missing token -> 401. Invalid token -> 403. Never logs token values.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing Authorization Bearer token")

    expected = _expected_token()
    if not expected:
        raise HTTPException(
            status_code=503,
            detail="TANNA_CONNECTOR_TOKEN is not configured on the server",
        )

    received = credentials.credentials.strip()
    if received != expected:
        raise HTTPException(status_code=403, detail="Invalid connector token")

    return True

"""API key authentication via the X-API-Key header."""

import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

API_KEY: str = os.getenv("API_KEY", "demo-key")

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(key: str = Security(api_key_header)) -> str:
    """Return the key, or raise 403 if it's missing or wrong."""
    if key is None or key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing or invalid API key",
        )
    return key

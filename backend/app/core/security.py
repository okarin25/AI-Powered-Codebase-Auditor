"""Lightweight API key authentication for the public API.

If API_KEY is unset in the environment, auth is disabled — convenient for
local development. Set API_KEY before deploying publicly, or anyone who
finds your Render URL can spend your Gemini quota and clone arbitrary repos
through your server.
"""

from fastapi import Header, HTTPException, status

from app.core.config import get_settings


async def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    settings = get_settings()

    if settings.api_key is None:
        return  # auth disabled (no API_KEY configured)

    if x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key.",
        )
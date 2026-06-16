from __future__ import annotations

import logging
import os

log = logging.getLogger(__name__)

import httpx  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from starlette.requests import Request  # noqa: E402

from app.limiter import _client_ip  # noqa: E402

_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
_TIMEOUT = 5.0


async def verify_turnstile(request: Request) -> None:
    """FastAPI dependency — verifies a Cloudflare Turnstile token before any paid LLM call.

    Reads ``TURNSTILE_SECRET`` from the environment; fails closed (503) if unset so a
    misconfigured deploy is immediately visible rather than silently unprotected.

    The token is expected as ``turnstile_token`` in the JSON request body.  Starlette
    caches the raw body bytes after the first read, so calling ``request.json()`` here
    does not interfere with FastAPI's subsequent parsing of the Pydantic body model.
    """
    secret = os.environ.get("TURNSTILE_SECRET")
    if not secret:
        log.warning("TURNSTILE_SECRET unset — skipping Turnstile verification (dev mode)")
        return

    try:
        body = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Invalid JSON body") from exc

    token: str = body.get("turnstile_token") or ""
    if not token:
        raise HTTPException(status_code=403, detail="Missing Turnstile token")

    ip = _client_ip(request)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                _VERIFY_URL,
                data={"secret": secret, "response": token, "remoteip": ip},
            )
            resp.raise_for_status()
            result = resp.json()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="Turnstile verification unavailable") from exc

    if not result.get("success"):
        raise HTTPException(status_code=403, detail="Turnstile challenge failed")

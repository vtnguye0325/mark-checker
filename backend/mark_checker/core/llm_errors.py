"""One place that turns an LLM provider error into an HTTP response.

The routes raise nothing for these: ``register_llm_error_handler`` puts the
mapping on the app, so no route carries a provider string.
"""

from __future__ import annotations

import logging

import openai
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

log = logging.getLogger(__name__)

# Words a Gemini free-tier 429 carries when the daily request quota, not the
# per-minute one, is the cap that fired. The daily wait is hours, so the user
# must see a different message and stop retrying.
_DAILY_QUOTA_MARKERS = ("per day", "perday", "requests per day", "daily limit")

# Words a 429 carries when the account has no billing balance, not when it is
# rate-limited. This never clears on its own, so it is an operator problem: a
# 503, not a "try again".
_BILLING_MARKERS = ("prepayment credits", "billing", "depleted", "check your plan")

_UNAVAILABLE = "The analysis service is unavailable right now."
_BUSY = "The analysis service is busy right now. Please try again shortly."
_DAILY_QUOTA = (
    "The analysis service has reached its free-tier limit for today. "
    "The quota resets at midnight Pacific time. Please try again tomorrow."
)


def _retry_after_seconds(exc: Exception) -> str | None:
    response = getattr(exc, "response", None)
    if response is None:
        return None
    return response.headers.get("retry-after")


def _matches(exc: Exception, markers: tuple[str, ...]) -> bool:
    text = str(getattr(exc, "message", "") or exc).lower()
    return any(marker in text for marker in markers)


def llm_error_response(exc: openai.APIError) -> JSONResponse:
    """Map a provider error to the response the frontend reads."""
    if isinstance(exc, openai.RateLimitError):
        if _matches(exc, _BILLING_MARKERS):
            # No balance on the account. This does not clear on a retry, so it
            # is a 503 and an operator alert, not a "try again".
            log.error("analyze: provider billing exhausted — check the API account")
            return JSONResponse(status_code=503, content={"detail": _UNAVAILABLE})
        if _matches(exc, _DAILY_QUOTA_MARKERS):
            log.warning("analyze: provider daily quota reached")
            return JSONResponse(status_code=429, content={"detail": _DAILY_QUOTA})
        retry_after = _retry_after_seconds(exc)
        log.warning("analyze: provider rate limit, retry-after=%s", retry_after)
        return JSONResponse(
            status_code=429,
            content={"detail": _BUSY},
            headers={"Retry-After": retry_after} if retry_after else None,
        )
    # Covers APITimeoutError and APIConnectionError, both subclasses.
    log.error("analyze: provider error: %s", exc)
    return JSONResponse(status_code=503, content={"detail": _UNAVAILABLE})


def register_llm_error_handler(app: FastAPI) -> None:
    """Handle every openai.APIError the routes let through."""

    async def _handler(request: Request, exc: Exception) -> JSONResponse:  # noqa: ARG001
        return llm_error_response(exc)

    app.add_exception_handler(openai.APIError, _handler)

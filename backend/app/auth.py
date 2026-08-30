from __future__ import annotations

import os
import time
from dataclasses import dataclass

import jwt
from fastapi import HTTPException
from google.auth.exceptions import GoogleAuthError, TransportError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request

# Fail closed at import, in the same style as db.DATABASE_URL and TURNSTILE_SECRET.
# A silent unauthenticated deploy is the worse outcome.
SESSION_SECRET = os.getenv("SESSION_SECRET")
if not SESSION_SECRET:
    raise RuntimeError("SESSION_SECRET is unset. Set it before you start the backend.")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
if not GOOGLE_CLIENT_ID:
    raise RuntimeError("GOOGLE_CLIENT_ID is unset. Set it before you start the backend.")

SESSION_TTL_HOURS = int(os.getenv("SESSION_TTL_HOURS", "168"))
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() != "false"
COOKIE_NAME = "session"
_ALGORITHM = "HS256"

# A browser clock a few seconds fast makes google-auth raise "Token used too
# early". Allow a small skew so a valid token is not rejected.
_CLOCK_SKEW_SECONDS = 10


@dataclass(frozen=True)
class SessionUser:
    id: str
    email: str


async def verify_google_id_token(token: str) -> dict:
    """Verify a Google ID token and return its claims.

    The verify call is blocking and, on the first call, fetches Google's
    certificates, so run it in the threadpool.
    """

    def _verify() -> dict:
        # Build the transport inside the worker thread. requests.Session is not
        # documented as thread-safe, and run_in_threadpool can run two of these
        # at once. Each call re-fetches Google's certs over HTTPS, which is fine
        # for a route that runs once per sign-in.
        return google_id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
            clock_skew_in_seconds=_CLOCK_SKEW_SECONDS,
        )

    try:
        claims = await run_in_threadpool(_verify)
    except (TransportError, ConnectionError) as exc:
        # Google is unreachable. This is not the user's fault, so the message
        # must not blame the user.
        raise HTTPException(status_code=503, detail="Cannot reach Google right now") from exc
    except (ValueError, GoogleAuthError) as exc:
        raise HTTPException(status_code=401, detail="Invalid Google token") from exc

    if not claims.get("email_verified"):
        raise HTTPException(status_code=401, detail="Google account email is not verified")
    return claims


def create_session_token(user_id: str, email: str) -> str:
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": now,
        "exp": now + SESSION_TTL_HOURS * 3600,
    }
    return jwt.encode(payload, SESSION_SECRET, algorithm=_ALGORITHM)


def current_user(request: Request) -> SessionUser:
    """FastAPI dependency — read and decode the session cookie.

    This dependency reads no database. The JWT is self-contained, so a Postgres
    outage cannot log every user out.
    """
    raw = request.cookies.get(COOKIE_NAME)
    if not raw:
        raise HTTPException(status_code=401, detail="Not signed in")
    try:
        payload = jwt.decode(raw, SESSION_SECRET, algorithms=[_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Session is invalid or expired") from exc

    sub = payload.get("sub")
    email = payload.get("email")
    if not sub or not email:
        raise HTTPException(status_code=401, detail="Session is invalid or expired")
    user = SessionUser(id=sub, email=email)
    # Step 7's rate-limit key function reads this, which saves a second decode.
    request.state.user = user
    return user

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    COOKIE_NAME,
    COOKIE_SECURE,
    SESSION_TTL_HOURS,
    SessionUser,
    create_session_token,
    current_user,
    verify_google_id_token,
)
from app.db import get_session
from app.limiter import limiter
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


class GoogleLoginRequest(BaseModel):
    credential: str


class PublicUser(BaseModel):
    id: str
    email: str
    name: str | None = None
    picture: str | None = None


@router.post("/google", response_model=PublicUser)
# A whole office behind one NAT IP shares this bucket, so keep it high enough
# that normal sign-ins never hit it. Google ID-token verification is the real
# abuse gate.
@limiter.limit("200/hour")
async def google_login(
    request: Request,  # noqa: ARG001  (slowapi reads the client IP off this)
    body: GoogleLoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> PublicUser:
    claims = await verify_google_id_token(body.credential)
    now = datetime.now(UTC)

    # Upsert on google_sub. on_conflict_do_update lets two parallel logins race
    # without a duplicate-key error.
    stmt = (
        insert(User)
        .values(
            google_sub=claims["sub"],
            email=claims["email"],
            name=claims.get("name"),
            picture=claims.get("picture"),
            created_at=now,
            last_login_at=now,
        )
        .on_conflict_do_update(
            index_elements=["google_sub"],
            set_={
                "email": claims["email"],
                "name": claims.get("name"),
                "picture": claims.get("picture"),
                "last_login_at": now,
            },
        )
        .returning(User.id)
    )
    result = await session.execute(stmt)
    user_id = result.scalar_one()
    await session.commit()

    token = create_session_token(
        user_id, claims["email"], claims.get("name"), claims.get("picture")
    )
    # SameSite=Lax blocks the cookie on cross-site POST, which is what protects
    # the check endpoints from CSRF. Keep every state-changing route on POST.
    response.set_cookie(
        COOKIE_NAME,
        token,
        max_age=SESSION_TTL_HOURS * 3600,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
        path="/",
    )
    return PublicUser(
        id=str(user_id),
        email=claims["email"],
        name=claims.get("name"),
        picture=claims.get("picture"),
    )


@router.post("/logout", status_code=204)
async def logout(response: Response) -> Response:
    # Match every attribute set in google_login so the browser clears the exact
    # cookie it stored.
    response.delete_cookie(
        COOKIE_NAME, path="/", httponly=True, samesite="lax", secure=COOKIE_SECURE
    )
    response.status_code = 204
    return response


@router.get("/me", response_model=PublicUser)
async def me(user: SessionUser = Depends(current_user)) -> PublicUser:
    return PublicUser(id=str(user.id), email=user.email, name=user.name, picture=user.picture)

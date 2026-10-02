from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import digest_session_token
from app.core.config import get_settings
from app.db.base import get_session
from app.db.models import Session, User


async def get_current_session(request: Request, db: AsyncSession) -> Session | None:
    token = request.cookies.get(get_settings().session_cookie_name)
    if not token:
        return None

    session = await db.scalar(
        select(Session).where(Session.token_digest == digest_session_token(token))
    )
    now = datetime.now(timezone.utc)
    if session is None or session.revoked_at is not None or session.expires_at <= now:
        return None

    session.last_used_at = now
    return session


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> User:
    session = await get_current_session(request, db)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    user = await db.get(User, session.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user

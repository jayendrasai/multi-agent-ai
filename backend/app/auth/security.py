import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models import Session

password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (InvalidHashError, VerificationError, VerifyMismatchError):
        return False


def digest_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def create_session(db: AsyncSession, user_id: UUID) -> str:
    settings = get_settings()
    raw_token = secrets.token_urlsafe(32)
    session = Session(
        user_id=user_id,
        token_digest=digest_session_token(raw_token),
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=settings.session_lifetime_seconds),
    )
    db.add(session)
    await db.flush()
    return raw_token

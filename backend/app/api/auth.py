import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import LoginRequest, OnboardingRequest, RegisterRequest, UserResponse
from app.auth.dependencies import get_current_session, get_current_user
from app.auth.security import create_session, hash_password, verify_password
from app.core.config import get_settings
from app.db.base import get_session
from app.db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


def _normalize(value: str) -> str:
    return value.strip().lower()


def _username_from_email(email: str) -> str:
    candidate = re.sub(r"[^a-z0-9_.-]", "", email.split("@", 1)[0].lower())[:70]
    return candidate or "user"


def _set_session_cookie(response: Response, token: str) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_lifetime_seconds,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="none",
        path="/",
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_session),
):
    email = _normalize(request.email)
    username = _normalize(request.username or _username_from_email(email))
    user = User(
        username=username,
        email=email,
        display_name=request.name.strip(),
        password_hash=hash_password(request.password),
    )
    db.add(user)
    try:
        await db.flush()
        token = await create_session(db, user.id)
        await db.commit()
        await db.refresh(user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to create an account with those details.",
        )

    _set_session_cookie(response, token)
    return user


@router.post("/login", response_model=UserResponse)
async def login(
    request: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_session),
):
    identifier = _normalize(request.identifier)
    user = await db.scalar(
        select(User).where(or_(User.email == identifier, User.username == identifier))
    )
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    token = await create_session(db, user.id)
    await db.commit()
    _set_session_cookie(response, token)
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_session),
):
    session = await get_current_session(request, db)
    if session is not None:
        session.revoked_at = datetime.now(timezone.utc)
        await db.commit()
    response.delete_cookie(get_settings().session_cookie_name, path="/")


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user


@router.patch("/onboarding", response_model=UserResponse)
async def complete_onboarding(
    request: OnboardingRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    user.workflow_interest = request.workflow_interest.strip()
    user.team_size = request.team_size.strip()
    user.experience_level = request.experience_level.strip()
    user.onboarding_completed = True
    await db.commit()
    await db.refresh(user)
    return user

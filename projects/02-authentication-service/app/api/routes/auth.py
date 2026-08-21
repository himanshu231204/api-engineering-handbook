from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.token import LogoutRequest, RefreshRequest, TokenPair
from app.schemas.user import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    ResetPasswordRequest,
    UserOut,
    UserRegister,
)
from app.security.dependencies import get_current_user
from app.services.auth_service import AuthService, EmailAlreadyRegisteredError, InvalidCredentialsError
from app.services.password_service import InvalidResetTokenError, PasswordService
from app.services.rate_limiter import RateLimiter
from app.services.token_service import InvalidRefreshTokenError, TokenReuseDetectedError, TokenService
from app.security.jwt import create_access_token
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

# Process-local rate limiters, keyed by client IP. See
# app/services/rate_limiter.py for why this isn't multi-worker-safe.
_login_limiter = RateLimiter(max_requests=5, window_seconds=60)
_forgot_limiter = RateLimiter(max_requests=3, window_seconds=60)


def _client_key(request: Request) -> str:
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, session: AsyncSession = Depends(get_session)) -> UserOut:
    service = AuthService(session)
    try:
        user = await service.register(email=payload.email, password=payload.password)
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email already registered") from exc
    await session.commit()
    return UserOut.model_validate(user)


@router.post("/login", response_model=TokenPair)
async def login(
    payload: LoginRequest, request: Request, session: AsyncSession = Depends(get_session)
) -> TokenPair:
    if not _login_limiter.allow(_client_key(request)):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="too many login attempts")

    auth_service = AuthService(session)
    try:
        user = await auth_service.authenticate(email=payload.email, password=payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    token_service = TokenService(session)
    access_token = create_access_token(user_id=user.id, role=user.role)
    refresh_token = await token_service.issue_refresh_token(user.id)
    await session.commit()
    return TokenPair(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, session: AsyncSession = Depends(get_session)) -> TokenPair:
    token_service = TokenService(session)
    try:
        user_id, new_refresh_token = await token_service.rotate(payload.refresh_token)
    except TokenReuseDetectedError as exc:
        await session.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    except InvalidRefreshTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    auth_service = AuthService(session)
    user = await auth_service.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="user no longer exists")

    access_token = create_access_token(user_id=user.id, role=user.role)
    await session.commit()
    return TokenPair(access_token=access_token, refresh_token=new_refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    payload: LogoutRequest,
    all_sessions: bool = Query(default=False, alias="all"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    token_service = TokenService(session)
    if all_sessions:
        await token_service.revoke_all_for_user(user.id)
    else:
        await token_service.revoke(payload.refresh_token)
    await session.commit()


@router.post("/password/forgot", response_model=ForgotPasswordResponse)
async def forgot_password(
    payload: ForgotPasswordRequest, request: Request, session: AsyncSession = Depends(get_session)
) -> ForgotPasswordResponse:
    if not _forgot_limiter.allow(_client_key(request)):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="too many reset attempts")

    auth_service = AuthService(session)
    user = await auth_service.get_by_email(payload.email)
    # Always return 200 with a generic message, whether or not the email
    # exists, to avoid leaking which emails are registered. The token is
    # only included in the response for local dev/testing (see README);
    # production would email it instead.
    if user is None:
        return ForgotPasswordResponse(detail="if that email exists, a reset link has been sent")

    password_service = PasswordService(session)
    reset_token = await password_service.issue_reset_token(user.id)
    await session.commit()
    return ForgotPasswordResponse(
        detail="if that email exists, a reset link has been sent", reset_token=reset_token
    )


@router.post("/password/reset", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(payload: ResetPasswordRequest, session: AsyncSession = Depends(get_session)) -> None:
    password_service = PasswordService(session)
    try:
        user_id = await password_service.consume_reset_token(payload.reset_token)
    except InvalidResetTokenError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    auth_service = AuthService(session)
    user = await auth_service.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user no longer exists")

    await auth_service.set_password(user, payload.new_password)
    # A password reset invalidates every existing refresh token -- an
    # attacker who stole a session shouldn't survive a password change.
    token_service = TokenService(session)
    await token_service.revoke_all_for_user(user.id)
    await session.commit()


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)

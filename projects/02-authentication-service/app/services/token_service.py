"""Refresh-token issuance, rotation, and reuse detection."""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.refresh_token import RefreshToken
from app.security.hashing import hash_token


class TokenReuseDetectedError(Exception):
    """Raised when a revoked refresh token is presented again -- a strong
    signal the token was stolen. The whole token family is revoked."""


class InvalidRefreshTokenError(Exception):
    pass


class TokenService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def issue_refresh_token(self, user_id: str) -> str:
        raw = secrets.token_urlsafe(48)
        record = RefreshToken(
            user_id=user_id,
            token_hash=hash_token(raw),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
        )
        self._session.add(record)
        await self._session.flush()
        return raw

    async def _get_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        result = await self._session.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
        return result.scalar_one_or_none()

    async def rotate(self, raw_token: str) -> tuple[str, str]:
        """Validate `raw_token`, revoke it, and issue a fresh pair.
        Returns (user_id, new_raw_refresh_token)."""
        token_hash = hash_token(raw_token)
        record = await self._get_by_hash(token_hash)
        if record is None:
            raise InvalidRefreshTokenError("unknown refresh token")

        if record.revoked_at is not None:
            # Reuse of an already-revoked token: revoke every other active
            # token for this user (the whole "family") since this is a
            # signal of theft, per the implementation plan step 5.
            await self._revoke_all_for_user(record.user_id)
            raise TokenReuseDetectedError("refresh token reuse detected; all sessions revoked")

        if record.expires_at < datetime.now(timezone.utc):
            raise InvalidRefreshTokenError("refresh token expired")

        new_raw = secrets.token_urlsafe(48)
        new_record = RefreshToken(
            user_id=record.user_id,
            token_hash=hash_token(new_raw),
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
        )
        self._session.add(new_record)
        await self._session.flush()

        record.revoked_at = datetime.now(timezone.utc)
        record.replaced_by = new_record.id
        await self._session.flush()

        return record.user_id, new_raw

    async def revoke(self, raw_token: str) -> None:
        record = await self._get_by_hash(hash_token(raw_token))
        if record is not None and record.revoked_at is None:
            record.revoked_at = datetime.now(timezone.utc)
            await self._session.flush()

    async def _revoke_all_for_user(self, user_id: str) -> None:
        result = await self._session.execute(
            select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        )
        now = datetime.now(timezone.utc)
        for record in result.scalars().all():
            record.revoked_at = now
        await self._session.flush()

    async def revoke_all_for_user(self, user_id: str) -> None:
        await self._revoke_all_for_user(user_id)

"""Password reset token issuance/consumption."""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.refresh_token import PasswordResetToken
from app.security.hashing import hash_token


class InvalidResetTokenError(Exception):
    pass


class PasswordService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def issue_reset_token(self, user_id: str) -> str:
        raw = secrets.token_urlsafe(32)
        record = PasswordResetToken(
            user_id=user_id,
            token_hash=hash_token(raw),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.reset_token_expire_minutes),
        )
        self._session.add(record)
        await self._session.flush()
        return raw

    async def consume_reset_token(self, raw_token: str) -> str:
        """Validates and marks the token used; returns the user_id."""
        token_hash = hash_token(raw_token)
        result = await self._session.execute(
            select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        )
        record: Optional[PasswordResetToken] = result.scalar_one_or_none()
        if record is None or record.used_at is not None:
            raise InvalidResetTokenError("reset token is invalid or already used")
        if record.expires_at < datetime.now(timezone.utc):
            raise InvalidResetTokenError("reset token expired")
        record.used_at = datetime.now(timezone.utc)
        await self._session.flush()
        return record.user_id

"""Registration/login/me business logic."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.security.hashing import hash_password, verify_password


class EmailAlreadyRegisteredError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: str) -> Optional[User]:
        return await self._session.get(User, user_id)

    async def register(self, *, email: str, password: str) -> User:
        existing = await self.get_by_email(email)
        if existing is not None:
            raise EmailAlreadyRegisteredError(email)
        user = User(email=email, password_hash=hash_password(password), role="user")
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def authenticate(self, *, email: str, password: str) -> User:
        user = await self.get_by_email(email)
        # Deliberately identical error for "no such user" and "wrong
        # password" -- don't let login reveal which emails are registered.
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("invalid email or password")
        return user

    async def set_password(self, user: User, new_password: str) -> None:
        user.password_hash = hash_password(new_password)
        await self._session.flush()

    async def list_users(self) -> list[User]:
        result = await self._session.execute(select(User).order_by(User.created_at))
        return list(result.scalars().all())

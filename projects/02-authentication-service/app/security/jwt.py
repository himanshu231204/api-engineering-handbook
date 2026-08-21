"""JWT access-token issuance and verification (HS256).

The README notes RS256/JWKS as an advanced improvement; this reference
implementation uses HS256 with a shared secret, which is the simpler
starting point the implementation plan calls for in step 3.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal

from jose import JWTError, jwt

from app.core.config import settings


class InvalidTokenError(Exception):
    pass


def create_access_token(*, user_id: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    claims = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(claims, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise InvalidTokenError("invalid or expired access token") from exc
    if payload.get("type") != "access":
        raise InvalidTokenError("token is not an access token")
    return payload

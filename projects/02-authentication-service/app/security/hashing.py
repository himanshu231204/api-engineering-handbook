"""Password hashing (bcrypt via passlib) and constant-time token hashing."""
from __future__ import annotations

import hashlib
import hmac

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def hash_token(raw_token: str) -> str:
    """SHA-256 the opaque refresh/reset token before storing it -- only the
    hash ever touches the database."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def constant_time_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)

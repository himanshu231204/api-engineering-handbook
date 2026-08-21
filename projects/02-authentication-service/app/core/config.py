"""Configuration read from environment variables. Never hardcode secrets --
see .env.example for every variable this service reads."""
from __future__ import annotations

import os
import secrets
import sys


def _require_or_warn(name: str, *, dev_fallback_len: int = 32) -> str:
    value = os.environ.get(name)
    if value:
        return value
    fallback = secrets.token_hex(dev_fallback_len)
    print(
        f"WARNING: {name} is not set. Using a random, process-only value "
        f"(see .env.example). Tokens/hashes will not survive a restart. "
        f"Never do this in production.",
        file=sys.stderr,
    )
    return fallback


class Settings:
    database_url: str = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./auth.db")
    jwt_secret_key: str = _require_or_warn("JWT_SECRET_KEY")
    jwt_algorithm: str = os.environ.get("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    refresh_token_expire_days: int = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "30"))
    reset_token_expire_minutes: int = int(os.environ.get("RESET_TOKEN_EXPIRE_MINUTES", "30"))
    login_rate_limit_per_minute: int = int(os.environ.get("LOGIN_RATE_LIMIT_PER_MINUTE", "5"))
    password_reset_rate_limit_per_minute: int = int(
        os.environ.get("PASSWORD_RESET_RATE_LIMIT_PER_MINUTE", "3")
    )


settings = Settings()

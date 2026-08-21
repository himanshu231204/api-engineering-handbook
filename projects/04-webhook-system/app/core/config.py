"""Configuration read from environment variables."""
from __future__ import annotations

import os


class Settings:
    database_url: str = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./webhooks.db")
    inbound_signing_secret: str = os.environ.get("INBOUND_SIGNING_SECRET", "dev-only-inbound-secret")
    replay_window_seconds: int = int(os.environ.get("REPLAY_WINDOW_SECONDS", "300"))
    max_delivery_attempts: int = int(os.environ.get("MAX_DELIVERY_ATTEMPTS", "8"))
    delivery_timeout_seconds: float = float(os.environ.get("DELIVERY_TIMEOUT_SECONDS", "5"))
    secret_rotation_grace_minutes: int = int(os.environ.get("SECRET_ROTATION_GRACE_MINUTES", "60"))
    base_backoff_seconds: float = float(os.environ.get("BASE_BACKOFF_SECONDS", "2"))


settings = Settings()

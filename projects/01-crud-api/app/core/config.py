"""Application configuration, read entirely from environment variables.

Never hardcode secrets or connection strings here -- see .env.example for
the variables this app reads.
"""
from __future__ import annotations

import os


class Settings:
    database_url: str = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///./bookshelf.db")
    app_name: str = os.environ.get("APP_NAME", "Bookshelf CRUD API")
    default_page_limit: int = int(os.environ.get("DEFAULT_PAGE_LIMIT", "20"))
    max_page_limit: int = int(os.environ.get("MAX_PAGE_LIMIT", "100"))


settings = Settings()

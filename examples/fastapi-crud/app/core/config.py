"""
Application configuration via Pydantic Settings.

Settings are read from environment variables and, in development, from a
local `.env` file (never commit a real `.env` -- see `.env.example` at the
project root for every variable this reads). See:
docs/03-building-apis/environment-variables.md
docs/03-building-apis/configuration-management.md
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "FastAPI CRUD Example"
    app_version: str = "1.0.0"
    debug: bool = False

    # SQLite by default so the example runs with zero external services.
    # Point this at a real Postgres URL in production, e.g.
    # postgresql+psycopg://user:password@host:5432/dbname
    database_url: str = "sqlite:///./tasks.db"

    # Comma-separated list of allowed CORS origins, e.g.
    # "http://localhost:3000,https://example.com". "*" allows any origin
    # (fine for a local example; do not do this in production).
    cors_origins: str = "*"

    default_page_size: int = 20
    max_page_size: int = 100

    @property
    def cors_origin_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached Settings instance.

    Used as a FastAPI dependency (`Depends(get_settings)`) so the
    environment / .env file is parsed once per process, and so tests can
    override it with `app.dependency_overrides[get_settings]`.
    """
    return Settings()

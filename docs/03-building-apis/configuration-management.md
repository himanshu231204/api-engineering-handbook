# Configuration Management

## Why This Matters

`environment-variables.md` showed you *why* configuration lives outside your code and how raw `os.environ` reads work. But scattering `os.environ.get("SOME_KEY")` calls across dozens of files is itself a maintainability problem: no single place shows what configuration the app needs, no type checking catches a misconfigured `"true"` string where an `int` was expected, and no validation catches a missing required value until the exact line of code that needs it finally runs — possibly deep into handling a real user's request.

**Configuration management** is about turning "a pile of environment variables" into a single, typed, validated, IDE-autocompletable object your whole application depends on.

## Core Concept

**Pydantic Settings** (the `pydantic-settings` package, the officially maintained successor to Pydantic v1's built-in `BaseSettings`) lets you define your app's entire configuration as a Pydantic model. It automatically:

1. Reads values from environment variables (and optionally a `.env` file) matching field names.
2. Validates and coerces types exactly like a regular Pydantic model (`"true"` → `True`, `"8000"` → `8000`).
3. Raises a clear validation error at startup if something required is missing or malformed.
4. Gives you one object (`settings.database_url`, `settings.debug`) with full IDE autocomplete, instead of stringly-typed `os.environ.get(...)` calls everywhere.

## Mental Model

Think of `Settings` as your application's **single, typed control panel**. Every dial and switch the app can be configured with lives on this one panel, each labeled with its type and default. Nobody reaches behind the panel to pull raw wires (`os.environ`) directly — they read the panel. This mirrors exactly how `request-validation-pydantic.md` treats request bodies: declare the shape once, get validation and clarity everywhere.

## How It Works

### Basic `Settings` class

```python
# core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Order API"
    debug: bool = False
    database_url: str                 # required — no default, must come from env
    secret_key: str                   # required
    openai_api_key: str | None = None  # optional feature
    request_timeout_seconds: float = 30.0


settings = Settings()  # reads env vars + .env once, at import time
```

Given `.env`:

```bash
DATABASE_URL=postgresql://postgres:pass@localhost:5432/myapp
SECRET_KEY=super-secret-value
DEBUG=true
```

`Settings()` automatically matches `DATABASE_URL` (env, uppercase) to `database_url` (field, lowercase) — matching is case-insensitive by default — coerces `"true"` to `True` for `debug`, and would raise a `ValidationError` immediately if `DATABASE_URL` or `SECRET_KEY` were missing.

### Per-environment configuration

A common pattern is one base `Settings` class plus environment-specific subclasses, selected by an `APP_ENV` variable:

```python
# core/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    debug: bool = False
    database_url: str
    secret_key: str
    openai_api_key: str | None = None
    cors_origins: list[str] = []


class DevelopmentSettings(Settings):
    debug: bool = True


class ProductionSettings(Settings):
    debug: bool = False


@lru_cache  # cache so Settings() (and env parsing) only happens once per process
def get_settings() -> Settings:
    import os
    env = os.environ.get("APP_ENV", "development")
    if env == "production":
        return ProductionSettings()
    return DevelopmentSettings()
```

`@lru_cache` is important: without it, every call to `get_settings()` would re-read and re-validate environment variables from scratch — wasteful, and if used as a FastAPI dependency, it defeats the point of a cheap, cached config object.

### Secrets vs. config

Not everything in `Settings` is equally sensitive. `app_name` and `request_timeout_seconds` are configuration; `secret_key` and `openai_api_key` are secrets. They're often stored the *same way* (environment variables) in small projects, but in production they frequently diverge:

- **Config** (non-sensitive): can live in a config file, a `ConfigMap` (Kubernetes), or plain env vars, and can safely appear in logs or debugging output.
- **Secrets** (sensitive): should come from a secret manager (AWS Secrets Manager, Vault, Doppler) injected as env vars at deploy time, and must **never** be logged, printed, or included in error messages — even in a `Settings.__repr__()`.

Pydantic Settings supports `SecretStr` for exactly this: it prevents the value from accidentally appearing in logs or reprs.

```python
from pydantic import SecretStr

class Settings(BaseSettings):
    secret_key: SecretStr
    openai_api_key: SecretStr | None = None

# settings.secret_key prints as SecretStr('**********') — use .get_secret_value() to access the real value
```

## Architecture

```mermaid
flowchart TD
    EnvVars["OS environment variables"] --> Settings
    DotEnv[".env file (dev only)"] --> Settings
    Settings["Settings (pydantic-settings)\nvalidated, typed, cached"] --> App["FastAPI app via Depends(get_settings)"]
    App --> Routes["Routes & services read settings.X"]
    Settings -.SecretStr fields never logged.-> Logs["Logging / error responses"]
```

## Request / Response Example

Configuration isn't part of the request/response cycle directly, but a misconfiguration surfaces immediately and loudly at startup rather than confusingly at request time:

```text
$ uvicorn main:app
Traceback (most recent call last):
  ...
pydantic_core._pydantic_core.ValidationError: 1 validation error for ProductionSettings
database_url
  Field required [type=missing, input_value={...}, input_type=dict]
```

Compare that to the alternative — a raw `os.environ["DATABASE_URL"]` call failing three requests into production traffic with a bare `KeyError` and no context about which setting or why.

## Code Example

```python
# core/config.py
from functools import lru_cache
from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    debug: bool = False
    database_url: str
    secret_key: SecretStr
    openai_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None
    cors_origins: list[str] = []
    request_timeout_seconds: float = 30.0

    @field_validator("app_env")
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"app_env must be one of {allowed}, got {v!r}")
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


# core/dependencies.py
from fastapi import Depends
from core.config import Settings, get_settings


# main.py
from fastapi import FastAPI, Depends
from core.config import get_settings, Settings

app = FastAPI()


@app.get("/config-check")
async def config_check(settings: Settings = Depends(get_settings)):
    # Safe to expose: never includes SecretStr values, which repr as asterisks.
    return {
        "app_env": settings.app_env,
        "debug": settings.debug,
        "has_openai_key": settings.openai_api_key is not None,
    }
```

## Production Considerations

- Cache `Settings` with `@lru_cache` (or build it once at import time) — parsing/validating env vars on every request is unnecessary overhead and can hide config drift mid-process.
- Use `SecretStr` for anything sensitive so it can never accidentally leak into logs, `repr()` output, or error messages.
- Validate `app_env`/environment name explicitly — a typo like `APP_ENV=produciton` silently falling back to development defaults in a real production deployment is a serious, hard-to-notice bug.
- In tests, override `get_settings` via `app.dependency_overrides` to inject a `Settings` instance pointing at a test database and dummy API keys — never point tests at real infrastructure.

## Common Mistakes

- Reading `os.environ` directly in scattered places *in addition to* having a `Settings` class — pick one source of truth.
- Not caching `get_settings()`, causing repeated environment re-parsing and, worse, subtle bugs if env vars are mutated mid-process (e.g., in certain test setups).
- Logging `settings` or `settings.dict()` wholesale during debugging — without `SecretStr`, this silently writes API keys and passwords to log files.
- Using one giant `Settings` class with no per-environment differentiation, then relying on manual, error-prone `if debug:` checks scattered throughout the codebase instead of a clean environment abstraction.

## Best Practices

- One `Settings` class (with environment-specific subclasses if needed) as the single source of truth for all configuration.
- Inject `Settings` via `Depends(get_settings)` like any other dependency (see `dependency-injection.md`) rather than importing a global `settings` object directly into every module — this keeps configuration testable and overridable.
- Use `SecretStr` for every credential, token, and key, without exception.
- Fail loudly and immediately (at startup, via Pydantic validation) rather than silently defaulting critical production values.

## AI Engineering Perspective

Configuration management is where you'll centralize every LLM provider's API key, base URL, default model name, and timeout in Part 15 — a single `Settings` class with fields like `openai_api_key`, `anthropic_api_key`, `default_llm_provider`, `llm_request_timeout_seconds`, `max_tokens_default`. This is what makes **model routing and fallback** (Part 15) tractable: your `LLMService` reads provider credentials and defaults from one validated `Settings` object rather than hunting through environment variables scattered across the codebase, and swapping the default provider in staging vs. production becomes a one-line config change instead of a code change. `SecretStr` is especially important here since LLM API keys are high-value targets — a leaked key can generate real, sometimes large, unauthorized billing.

## Exercises

**Beginner**
1. Convert a set of `os.environ.get(...)` calls into a `Settings(BaseSettings)` class with proper types and defaults, and inject it into one route via `Depends`.

**Intermediate**
2. Add a `SecretStr` field for an API key, print `settings` to confirm the value doesn't leak in the repr, then correctly access the real value with `.get_secret_value()`.

**Advanced**
3. Build `DevelopmentSettings`/`ProductionSettings` subclasses with different `cors_origins` and `debug` defaults, selected via `APP_ENV`, and write a test that overrides `get_settings` to inject a `TestSettings` pointing at an in-memory database.

## Key Takeaways

- Pydantic Settings turns scattered environment variables into one typed, validated, centrally-defined configuration object.
- Misconfiguration should fail loudly at startup, not silently or deep inside a request handler.
- `SecretStr` protects credentials from accidentally leaking into logs or error output.
- Inject `Settings` via FastAPI's dependency system so it's overridable in tests, exactly like a database session.
- See the full working version in `../../examples/fastapi-crud/`.

Previous: `environment-variables.md` · Next: `openapi-documentation.md`.

# Environment Variables

## Why This Matters

Your API needs to behave differently depending on where it runs: a local database URL on your laptop, a different one in staging, a different one in production; debug logging on locally, off in production; a test LLM API key locally, a real one in production. If any of this is hardcoded into your source code, you're one `git push` away from leaking a production secret into a public repository, or — just as bad — accidentally running production traffic against a staging database because someone forgot to change a hardcoded string before deploying.

Environment variables solve this by separating **code** (what the app does) from **configuration** (how it's set up in a given environment) — a principle formalized as factor #3 of the [12-factor app](https://12factor.net) methodology: *store config in the environment*.

## Core Concept

An **environment variable** is a key-value pair set outside your application, in the operating system or process environment, that your code reads at runtime. In Python:

```python
import os
database_url = os.environ["DATABASE_URL"]     # raises KeyError if missing
database_url = os.environ.get("DATABASE_URL")  # returns None if missing
```

The critical property: the *same code* can run in dev, staging, and production, each with different environment variables, and never needs to be edited between deployments.

## Mental Model

Think of your application code as a **machine with unlabeled input sockets**, and environment variables as the **plugs** you insert at boot time depending on where the machine is running. The machine (code) never changes; only the plugs (config) do. This is exactly why you should never hardcode a value that could plausibly differ between environments — every hardcoded database URL, API key, or feature flag is a socket you welded shut.

## How It Works

### `.env` files and `python-dotenv`

Setting real OS-level environment variables for local development is tedious, so most projects use a `.env` file — a plain text file of `KEY=value` lines — loaded automatically by a library like `python-dotenv`:

```bash
# .env  (NEVER commit this file)
DATABASE_URL=postgresql://postgres:localpass@localhost:5432/myapp_dev
SECRET_KEY=dev-only-not-a-real-secret
OPENAI_API_KEY=sk-dev-xxxxxxxxxxxx
DEBUG=true
```

```python
from dotenv import load_dotenv
load_dotenv()  # reads .env and populates os.environ, if not already set

import os
debug = os.environ.get("DEBUG", "false").lower() == "true"
```

In production, you typically **don't** ship a `.env` file at all — the hosting platform (a container orchestrator, a PaaS like Render or Railway, a CI/CD pipeline) injects real environment variables directly into the process, and `load_dotenv()` simply finds nothing to load, which is fine — `os.environ` is already populated by the platform.

### `.env.example`

Commit a `.env.example` (no real values) so new contributors know exactly which variables the app needs, without ever seeing real secrets:

```bash
# .env.example — safe to commit
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
SECRET_KEY=
OPENAI_API_KEY=
DEBUG=true
```

### `.gitignore`

```
.env
.env.local
.env.*.local
```

This is non-negotiable. A `.env` file committed to git history remains recoverable forever, even if you delete it in a later commit — rotating the leaked secret is the only real fix once it happens.

## Architecture

```mermaid
flowchart LR
    subgraph Local Dev
        DotEnv[".env file"] --> Process1["python process"]
    end
    subgraph CI/CD
        Secrets["CI secret store\n(GitHub Actions secrets, etc.)"] --> Process2["python process"]
    end
    subgraph Production
        PlatformEnv["Platform env vars\n(container orchestrator / PaaS)"] --> Process3["python process"]
    end
    Process1 --> App["Same application code"]
    Process2 --> App
    Process3 --> App
```

The same codebase, unmodified, runs correctly in all three environments because it only ever reads `os.environ` — it never knows or cares *how* those variables got set.

## Request / Response Example

Environment variables aren't part of the HTTP contract directly, but they determine behavior visible in responses. For example, with `DEBUG=true` locally:

```http
GET /crash-test HTTP/1.1
```

```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{"detail": "ZeroDivisionError: division by zero", "traceback": "Traceback (most recent call last)..."}
```

With `DEBUG=false` in production, the same crash returns:

```http
HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{"error": {"code": "internal_error", "message": "An unexpected error occurred"}}
```

Same code, different environment variable, deliberately different (and safer) client-visible behavior — see `exception-handling.md`.

## Code Example

```python
# core/env.py
import os
from dotenv import load_dotenv

# load_dotenv() is a no-op in production if there's no .env file to find —
# real env vars injected by the platform are already in os.environ.
load_dotenv()


def get_required_env(key: str) -> str:
    """Fail fast and loudly at startup if a required variable is missing,
    rather than failing confusingly mid-request later."""
    value = os.environ.get(key)
    if value is None or value == "":
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


def get_bool_env(key: str, default: bool = False) -> bool:
    value = os.environ.get(key)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


# usage at startup
DATABASE_URL = get_required_env("DATABASE_URL")
SECRET_KEY = get_required_env("SECRET_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")  # optional: feature may be disabled without it
DEBUG = get_bool_env("DEBUG", default=False)
```

```python
# main.py
from fastapi import FastAPI
from core.env import DATABASE_URL, DEBUG  # fails fast at import time if misconfigured

app = FastAPI(debug=DEBUG)
```

Note: in a real project you'd typically wrap this pattern in **Pydantic Settings** instead of raw `os.environ` calls — that's the subject of `configuration-management.md`, which builds directly on top of this chapter.

## Production Considerations

- **Never commit `.env` files.** Use `.gitignore` from day one, before the first secret is ever written to disk.
- **Fail fast at startup**, not mid-request, when a required environment variable is missing — a crash on boot is far easier to diagnose than a `NoneType has no attribute` error three requests into production traffic.
- **Use your platform's secret manager for real secrets** (AWS Secrets Manager, GCP Secret Manager, Doppler, Vault, or your PaaS's built-in encrypted env vars) rather than plain environment variables where you can — env vars are often visible to anything that can read the process environment or is written to logs/crash dumps.
- **Rotate secrets that leak, immediately** — assume any secret that ever touched a public git history or a public CI log is permanently compromised.
- **Different `.env` per environment** (`.env.development`, `.env.staging`, loaded conditionally), never one `.env` manually edited between deploys.

## Common Mistakes

- Hardcoding a "temporary" API key or database URL directly in code "just to test," then forgetting to remove it before committing.
- Committing `.env` once, then adding it to `.gitignore` later — the file is still in git history and needs to be purged (and the secret rotated) separately.
- Reading environment variables scattered throughout the codebase with `os.environ.get(...)` calls instead of centralizing them — makes it impossible to know, at a glance, what configuration the app actually depends on.
- Silently defaulting a required secret to an empty string or `None` and letting the failure surface deep inside a request instead of at startup.

## Best Practices

- Centralize all environment variable reads in one module (or, better, one Pydantic Settings class — see `configuration-management.md`) rather than scattering `os.environ.get(...)` calls throughout the codebase.
- Maintain a `.env.example` with every key your app needs, no real values, committed to git.
- Validate required variables exist at application startup, not lazily on first use.
- Treat any variable holding a credential, token, or key as a secret, even in "internal" or "dev" environments — dev secrets leak too.

## AI Engineering Perspective

AI-backed APIs typically depend on multiple provider API keys (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `COHERE_API_KEY`, a vector database URL/token) — all of which are exactly as sensitive as a database password, sometimes more, since a leaked LLM API key can rack up real financial cost within minutes if abused. The same discipline in this chapter — never hardcode, never commit, fail fast on missing keys, use a secret manager in production — is what Part 15 (Production AI Systems) builds on for managing multiple providers' credentials and rotating them without downtime (e.g., supporting two valid `OPENAI_API_KEY` values simultaneously during a rotation window).

## Exercises

**Beginner**
1. Create a `.env` file with `DATABASE_URL` and `DEBUG`, load it with `python-dotenv`, and print both values at startup. Add `.env` to `.gitignore` and create a matching `.env.example`.

**Intermediate**
2. Write a `get_required_env` helper that raises a clear `RuntimeError` at import time if a variable is missing, and demonstrate the app refusing to start when `SECRET_KEY` is unset.

**Advanced**
3. Set up three `.env` files (`.env.development`, `.env.staging`, `.env.production` — the last with fake placeholder values only) and write a small loader that picks the right one based on an `APP_ENV` variable, falling back sensibly if `APP_ENV` is unset.

## Key Takeaways

- Environment variables separate code from configuration, letting the same code run correctly across dev, staging, and production.
- `.env` files are a local-development convenience; production should get real config from the platform or a secret manager, never a checked-in file.
- Fail fast at startup when required configuration is missing — don't let it surface as a confusing runtime error later.
- Never commit `.env`; always commit a values-free `.env.example`.
- See the full working version in `../../examples/fastapi-crud/`.

Previous: `project-architecture.md` · Next: `configuration-management.md`.

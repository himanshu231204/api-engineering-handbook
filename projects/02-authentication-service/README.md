# Project 2 — Authentication Service

## Goal

Build a standalone authentication service — separate from any business API — that other projects in this handbook (Project 3 onward) can plug into. This project forces you to actually implement, not just read about, password hashing, JWT issuance and verification, refresh-token rotation, and role-based access control. Treating auth as its own service (rather than bolting it onto a monolith) also teaches you the real-world pattern of service-to-service trust that shows up throughout Parts 11 and 18.

## Builds On

- [Part 5 — Authentication & Authorization](../../docs/05-authentication-authorization/README.md)
- Specifically: [authentication vs authorization](../../docs/05-authentication-authorization/authentication-vs-authorization.md), [sessions and cookies](../../docs/05-authentication-authorization/sessions-and-cookies.md), [bearer tokens](../../docs/05-authentication-authorization/bearer-tokens.md), [JWT deeply explained](../../docs/05-authentication-authorization/jwt-deeply-explained.md), [access vs refresh tokens](../../docs/05-authentication-authorization/access-vs-refresh-tokens.md), [OAuth 2.0](../../docs/05-authentication-authorization/oauth2.md), [RBAC](../../docs/05-authentication-authorization/rbac.md), [API keys](../../docs/05-authentication-authorization/api-keys.md)

## Requirements

- User registration with email + password, enforcing password strength and hashing with bcrypt/argon2 (never plaintext, ever).
- Login issues a short-lived JWT access token and a long-lived, rotating refresh token.
- Refresh endpoint exchanges a valid refresh token for a new access token and rotates the refresh token (invalidating the old one).
- Logout invalidates the current refresh token (and optionally all sessions for the user).
- Password reset flow via a time-limited, single-use reset token (emailed in production; returned in the response body for local dev/testing).
- Role-based access control: at minimum `user` and `admin` roles, with an example protected admin-only route.
- Optional: OAuth 2.0 social login (Google/GitHub) that creates or links a local account.
- Every other project's API can validate tokens issued by this service (via a shared JWT secret/JWKS endpoint) without re-implementing auth.
- Rate limiting on login and password-reset endpoints to blunt brute-force and enumeration attacks.

## Architecture

```mermaid
flowchart LR
    Client[Client App] -->|register/login| Auth[Auth Service]
    Auth --> Hash[Password Hasher\n(bcrypt/argon2)]
    Auth --> TokenSvc[Token Service\n(JWT sign/verify)]
    Auth --> DB[(Users, Roles,\nRefreshTokens, ResetTokens)]
    Auth -->|JWKS / public key| Other[Other API Services\n(Projects 3, 6, 7, 8, 9...)]
    Client -->|Bearer access_token| Other
    Other -->|verify signature locally| TokenSvc
    Auth -.->|optional OAuth redirect| Provider[Google / GitHub OAuth]
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Create a new user account. Hashes password, sends verification email (or logs it locally). |
| POST | `/auth/login` | Verify credentials, issue access + refresh tokens. |
| POST | `/auth/refresh` | Exchange a valid refresh token for a new access/refresh token pair; rotates and revokes the old refresh token. |
| POST | `/auth/logout` | Revoke the current refresh token (or all tokens for the user with `?all=true`). |
| POST | `/auth/password/forgot` | Generate a single-use, time-limited password reset token. |
| POST | `/auth/password/reset` | Consume a reset token and set a new password; invalidates all existing refresh tokens. |
| GET | `/auth/me` | Return the authenticated user's profile, derived from the access token. |
| GET | `/auth/.well-known/jwks.json` | Public key(s) for other services to verify access tokens (if using asymmetric signing). |
| GET | `/auth/oauth/{provider}/redirect` | Start OAuth 2.0 authorization flow with a social provider. |
| GET | `/auth/oauth/{provider}/callback` | Handle provider callback, create/link account, issue tokens. |
| GET | `/admin/users` | Admin-only: list all users (demonstrates RBAC enforcement). |

## Database Schema

```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT,                    -- NULL for OAuth-only accounts
    role            TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user','admin')),
    is_verified     BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE refresh_tokens (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash      TEXT UNIQUE NOT NULL,     -- store a hash, never the raw token
    issued_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at      TIMESTAMPTZ NOT NULL,
    revoked_at      TIMESTAMPTZ,
    replaced_by     UUID REFERENCES refresh_tokens(id)
);

CREATE TABLE password_reset_tokens (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash      TEXT UNIQUE NOT NULL,
    expires_at      TIMESTAMPTZ NOT NULL,
    used_at         TIMESTAMPTZ
);

CREATE TABLE oauth_identities (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    provider        TEXT NOT NULL,             -- 'google', 'github'
    provider_user_id TEXT NOT NULL,
    UNIQUE (provider, provider_user_id)
);
```

## Suggested Folder Structure

```
02-authentication-service/
├── app/
│   ├── main.py
│   ├── api/routes/
│   │   ├── auth.py
│   │   ├── oauth.py
│   │   └── admin.py
│   ├── schemas/
│   │   ├── user.py
│   │   └── token.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── token_service.py
│   │   └── password_service.py
│   ├── security/
│   │   ├── hashing.py
│   │   ├── jwt.py
│   │   └── dependencies.py       # get_current_user, require_role
│   ├── models/
│   │   ├── user.py
│   │   └── refresh_token.py
│   ├── db/session.py
│   └── core/config.py
├── tests/
│   ├── test_register.py
│   ├── test_login.py
│   ├── test_refresh_rotation.py
│   └── test_rbac.py
├── requirements.txt
└── README.md
```

## Step-by-Step Implementation Plan

1. Scaffold FastAPI project, Postgres via Docker Compose, and the `users` table/migration.
2. Implement password hashing utilities (argon2 or bcrypt) and a `/auth/register` endpoint with strength validation.
3. Implement JWT signing/verification (start with HS256, note the tradeoffs vs RS256 for multi-service verification) per [JWT deeply explained](../../docs/05-authentication-authorization/jwt-deeply-explained.md).
4. Implement `/auth/login`: verify password, issue access token (short TTL, e.g. 15 min) and refresh token (long TTL, e.g. 30 days), storing only a hash of the refresh token.
5. Implement `/auth/refresh` with rotation: validate the incoming refresh token against its stored hash, revoke it, issue a new pair, and detect reuse of a revoked token as a signal of theft (revoke the whole token family).
6. Implement `/auth/logout` and the `get_current_user` FastAPI dependency that verifies the `Authorization: Bearer` header.
7. Add `require_role("admin")` dependency and a protected `/admin/users` route to prove RBAC works end to end, per [RBAC](../../docs/05-authentication-authorization/rbac.md).
8. Implement password reset: generate a single-use token, hash it before storing, expose `/auth/password/forgot` and `/auth/password/reset`.
9. Add rate limiting (in-memory or Redis-backed) to `/auth/login` and `/auth/password/forgot` to prevent brute-force/enumeration.
10. (Optional) Implement OAuth 2.0 login with one provider using the authorization code flow, linking to an existing user by verified email or creating a new one.
11. Expose a JWKS endpoint (if using RS256) so downstream services can verify tokens without calling this service on every request.
12. Write integration tests for the full lifecycle: register → login → call protected route → refresh → logout → refresh again (should fail).

## Advanced Improvements

- Switch to RS256/ES256 with key rotation and a proper JWKS endpoint with `kid` support.
- Add device/session tracking so users can see and revoke individual active sessions.
- Add email verification as a hard requirement before login.
- Add multi-factor authentication (TOTP) as an optional second factor.
- Add account lockout after N failed login attempts with exponential backoff.
- Publish this service's OpenAPI schema and a thin client SDK other projects can import.

## Production Checklist

- [ ] Passwords hashed with argon2id or bcrypt (cost factor tuned), never logged or returned in any response.
- [ ] Refresh tokens stored as hashes only; reuse of a revoked refresh token triggers full session-family revocation.
- [ ] Access tokens short-lived (minutes); refresh tokens long-lived but rotated on every use.
- [ ] Rate limiting and account lockout on login/reset endpoints, per [rate limiting](../../docs/06-production-reliability/rate-limiting.md).
- [ ] Secrets (JWT signing keys, OAuth client secrets) loaded from a secrets manager, not `.env` in production.
- [ ] CSRF protection if refresh tokens are ever stored in cookies rather than only returned to a mobile/SPA client.
- [ ] Structured audit logging for login, logout, password reset, and role changes.
- [ ] Timing-safe comparison for token/password checks to avoid timing side-channels.
- [ ] Full test coverage of the refresh-rotation and token-reuse-detection logic — this is the most bug-prone part.
- [ ] Documented token contract (claims, expiry, algorithm) that other services can rely on without reading this service's source.

## Related

- [Project index (Part 20)](../../docs/20-capstone-projects/README.md)
- [Handbook home](../../README.md)
- Consumed by: [Project 3 — Payment API](../03-payment-api/README.md), [Project 10 — Production AI SaaS](../10-production-ai-saas/README.md)

## Reference Implementation

A working reference implementation lives in this directory under `app/` and `tests/` (FastAPI + Pydantic v2 + SQLAlchemy async + SQLite via `aiosqlite`, HS256 JWTs via `python-jose`, bcrypt hashing via `passlib`). It covers registration with password-strength validation, login, refresh-token rotation with reuse detection (a revoked token being replayed revokes the whole token family), logout, password reset (which revokes all existing sessions), `GET /auth/me`, RBAC via a `require_role("admin")` dependency and a protected `/admin/users` route, and a process-local rate limiter on `/auth/login` and `/auth/password/forgot`. **Not implemented**: OAuth social login and the JWKS/RS256 endpoint — both are called out as optional/advanced-improvement items above, so this reference uses HS256 with a shared secret instead.

To run it:

```bash
cd projects/02-authentication-service
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set a real JWT_SECRET_KEY
uvicorn app.main:app --reload
# in another shell:
pytest
```

**Verification status**: every file under `app/` and `tests/` was byte-compiled successfully with `python3 -m py_compile`. `pip install` and `pytest` could not actually be run in the sandbox this was built in (outbound access to PyPI was network-blocked), so the test suite has **not** been executed end-to-end — treat it as syntax-verified only until you run `pytest` yourself.

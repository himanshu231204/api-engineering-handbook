# JWT Access/Refresh Authentication

Accompanies [Part 5 — Authentication & Authorization](../../docs/05-authentication-authorization/README.md),
especially [JWT Deeply Explained](../../docs/05-authentication-authorization/jwt-deeply-explained.md),
[Access vs Refresh Tokens](../../docs/05-authentication-authorization/access-vs-refresh-tokens.md), and
[Bearer Tokens](../../docs/05-authentication-authorization/bearer-tokens.md).

## What this demonstrates

A complete, minimal JWT authentication flow in a single FastAPI file:

- `POST /register` — create a user; the password is hashed with `passlib` (bcrypt) and
  the plaintext is never stored.
- `POST /login` — verify credentials and issue **both** a short-lived access token and a
  longer-lived refresh token.
- `POST /refresh` — trade a valid refresh token for a new access token, without making
  the user log in again.
- `GET /me` — a protected route: reachable only with a valid, non-expired access token
  sent as `Authorization: Bearer <token>`.

The two token types are deliberately encoded with a `"type": "access"` /
`"type": "refresh"` claim and checked on every decode — `/refresh` explicitly rejects an
access token, and `/me` explicitly rejects a refresh token, so one token can't be used in
place of the other.

User storage is a plain in-memory `dict`, so the auth flow is the whole point — no
database setup to distract from it.

## Prerequisites

- Python 3.11+

## How to run it

```bash
cd examples/authentication
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and set JWT_SECRET_KEY to a real random value:
python -c "import secrets; print(secrets.token_hex(32))"

uvicorn main:app --reload
```

If you skip the `.env` setup entirely, the app still starts — it falls back to a random,
process-only secret and prints a loud warning. That's fine for a five-minute experiment,
never for anything real.

## Try it with curl

```bash
# Register
curl -s -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "ada", "password": "correct-horse-battery"}'

# Log in -- issues an access + refresh token
curl -s -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "ada", "password": "correct-horse-battery"}'
# {"access_token": "...", "refresh_token": "...", "token_type": "bearer"}

# Call the protected route with the access token
ACCESS=<paste the access_token here>
curl -s http://127.0.0.1:8000/me -H "Authorization: Bearer $ACCESS"

# Without a token, or with a garbage token -- both return 401
curl -s -i http://127.0.0.1:8000/me
curl -s -i http://127.0.0.1:8000/me -H "Authorization: Bearer not-a-real-token"

# Get a new access token from the refresh token, without logging in again
REFRESH=<paste the refresh_token here>
curl -s -X POST http://127.0.0.1:8000/refresh \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\": \"$REFRESH\"}"
```

## Things to try

1. **Watch a token actually expire.** Set `ACCESS_TOKEN_EXPIRE_MINUTES=0` (or wait past
   the default 15 minutes), call `/me`, and see the 401 — then use `/refresh` to get a
   working access token again without re-entering a password.
2. **Try using a refresh token where an access token belongs.** Send the `refresh_token`
   value as the `Authorization: Bearer` header to `/me` — it's rejected because of the
   `"type"` claim check in `decode_token`. Remove that check and see the (bad) alternative:
   any refresh token becomes a permanently-valid access token.
3. **Add refresh token rotation.** Right now `/refresh` can be called repeatedly with the
   same refresh token until it expires. A more production-ready design issues a *new*
   refresh token on every `/refresh` call and invalidates the old one (usually via a
   server-side denylist or a stored token version/generation number) — try implementing
   that and think about what state you'd need to add beyond the in-memory `_users` dict.

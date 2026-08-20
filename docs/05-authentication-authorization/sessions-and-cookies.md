# Sessions and Cookies

## Why This Matters

HTTP is stateless — every request is, in principle, independent of every other. But almost every real application needs to remember "this request belongs to the same logged-in user as the last one." Sessions and cookies were the original, and are still the most widely deployed, answer to that problem. Understanding them well matters for two reasons: first, they're still the right choice for classic server-rendered web apps and many first-party web dashboards; second, understanding *why* they work (and where they're fragile — session fixation, CSRF exposure, scaling stateful servers) is what lets you make an informed choice between sessions and token-based auth like [bearer tokens](bearer-tokens.md) and [JWTs](jwt-deeply-explained.md).

## Core Concept

A **session** is server-side state associated with a particular user's ongoing interaction with your application — typically stored in memory, a database, or a fast key-value store like Redis, keyed by a random **session ID**.

A **cookie** is the transport mechanism: a small piece of data the server asks the browser to store and automatically resend on every subsequent request to that domain. The session ID is stored in a cookie; the actual session *data* (user ID, roles, cart contents, etc.) lives server-side, looked up by that ID.

This is the crucial architectural point: **the cookie holds a reference, not the truth.** The truth lives on the server. That's what makes sessions revocable instantly (just delete the server-side record) — a property that stateless tokens like JWTs famously lack.

## Mental Model

Think of a coat check at a theater. You hand over your coat (your credentials, at login time) and get back a numbered ticket (the session cookie). The ticket itself is worthless information — it's just a number — but presenting it lets the attendant (the server) look up *your* coat (your session data) from the rack. If you lose the ticket, or someone steals it, whoever holds it can claim your coat. And if the theater decides your ticket is no longer valid, they simply cross it off their list — the ticket itself doesn't need to change.

## How It Works

1. **Login**: client submits credentials (username/password). Server verifies them.
2. **Session creation**: server generates a cryptographically random session ID, creates a session record (`session_id -> {user_id, created_at, expires_at, ...}`) in its session store, and sends the ID back in a `Set-Cookie` header.
3. **Subsequent requests**: the browser automatically attaches the cookie on every request to the matching domain/path. The server looks up the session ID in its store, finds the associated user, and treats the request as authenticated.
4. **Logout / expiry**: server deletes the session record (or lets it expire via TTL). The cookie may still exist in the browser, but it now resolves to nothing — instant, server-side revocation.

### Cookie attributes that matter for security

- **`HttpOnly`** — the cookie is inaccessible to JavaScript (`document.cookie` cannot read it). This is the primary defense against session theft via XSS: even if an attacker injects a script, it can't exfiltrate the cookie.
- **`Secure`** — the browser will only send the cookie over HTTPS, never plaintext HTTP, preventing network eavesdropping from capturing it.
- **`SameSite`** — controls whether the cookie is sent on cross-site requests. `Strict` never sends it cross-site; `Lax` (the modern browser default) sends it on top-level navigations but not on cross-site subrequests/form posts; `None` (requires `Secure`) sends it everywhere, which you'd only use for legitimate cross-site embedding scenarios. `SameSite=Lax` or `Strict` is your primary structural defense against CSRF, discussed further in [Part 10 — API Security](../10-api-security/README.md).
- **`Max-Age` / `Expires`** — how long the browser retains the cookie. Session cookies (no expiry set) die when the browser closes; persistent cookies survive restarts.
- **`Path` / `Domain`** — scope which requests the cookie is attached to.

### Session fixation

A specific, easy-to-miss vulnerability: if an attacker can *set* a victim's session ID before login (e.g., via a crafted link containing `?session_id=attacker-known-value`, or if the app accepts a client-supplied session ID at all), and the application doesn't rotate the session ID upon successful authentication, the attacker can later use that same, now-authenticated session ID to hijack the victim's session. **The fix is structural**: always generate a brand-new session ID at the moment of privilege escalation (login, or any elevation like admin re-auth), never reuse a pre-login session ID, and never accept a client-supplied session ID as valid without server-side issuance.

## Architecture

```mermaid
sequenceDiagram
    participant Browser
    participant API as API Server
    participant Store as Session Store (Redis/DB)

    Browser->>API: POST /login (username, password)
    API->>API: Verify credentials
    API->>Store: Create session {user_id, expires_at}
    Store-->>API: session_id = "sk_9f2e..."
    API-->>Browser: 200 OK\nSet-Cookie: session_id=sk_9f2e...; HttpOnly; Secure; SameSite=Lax

    Note over Browser: Cookie stored, resent automatically

    Browser->>API: GET /account/profile\nCookie: session_id=sk_9f2e...
    API->>Store: Look up sk_9f2e...
    Store-->>API: {user_id: 123, expires_at: ...}
    API-->>Browser: 200 OK (profile data)

    Browser->>API: POST /logout\nCookie: session_id=sk_9f2e...
    API->>Store: Delete session sk_9f2e...
    API-->>Browser: 200 OK\nSet-Cookie: session_id=; Max-Age=0
```

## Request / Response Example

Login response setting a secure session cookie:

```http
POST /login HTTP/1.1
Host: api.example.com
Content-Type: application/json

{"email": "user@example.com", "password": "correct horse battery staple"}
```

```http
HTTP/1.1 200 OK
Set-Cookie: session_id=sk_9f2e7c1a4b8d; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=86400
Content-Type: application/json

{"status": "authenticated", "user_id": 123}
```

An authenticated follow-up request — the browser attaches the cookie automatically, no client-side JavaScript required:

```http
GET /account/profile HTTP/1.1
Host: api.example.com
Cookie: session_id=sk_9f2e7c1a4b8d
```

## Code Example

```python
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Depends, HTTPException, Request, Response

app = FastAPI()

# In production this is Redis or a database table with a TTL index,
# never an in-process dict (it won't survive restarts or scale past one instance).
SESSION_STORE: dict[str, dict] = {}
SESSION_TTL = timedelta(hours=24)
COOKIE_NAME = "session_id"
# Whether cookies require HTTPS - only False in local dev, always True in production.
COOKIE_SECURE = os.environ.get("ENV", "production") != "development"


def create_session(user_id: int) -> str:
    # secrets.token_urlsafe uses a CSPRNG - never use random.random() or uuid4()
    # derived from a weak source for anything security-sensitive.
    session_id = secrets.token_urlsafe(32)
    SESSION_STORE[session_id] = {
        "user_id": user_id,
        "expires_at": datetime.now(timezone.utc) + SESSION_TTL,
    }
    return session_id


def get_current_user(request: Request) -> dict:
    session_id = request.cookies.get(COOKIE_NAME)
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    session = SESSION_STORE.get(session_id)
    if not session or session["expires_at"] < datetime.now(timezone.utc):
        SESSION_STORE.pop(session_id, None)
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    return session


@app.post("/login")
async def login(response: Response, email: str, password: str):
    user = authenticate(email, password)  # verifies against hashed password in DB
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # IMPORTANT: always issue a brand-new session ID on login, even if the
    # client already sent one. Reusing a pre-login session ID is what
    # enables session fixation attacks.
    session_id = create_session(user["id"])

    response.set_cookie(
        key=COOKIE_NAME,
        value=session_id,
        httponly=True,       # blocks JavaScript access -> mitigates XSS-based theft
        secure=COOKIE_SECURE,  # only sent over HTTPS
        samesite="lax",      # blocks most cross-site (CSRF) submission vectors
        max_age=int(SESSION_TTL.total_seconds()),
        path="/",
    )
    return {"status": "authenticated"}


@app.post("/logout")
async def logout(response: Response, request: Request):
    session_id = request.cookies.get(COOKIE_NAME)
    if session_id:
        SESSION_STORE.pop(session_id, None)  # server-side revocation - instant
    response.delete_cookie(COOKIE_NAME, path="/")
    return {"status": "logged out"}


@app.get("/account/profile")
async def profile(session: dict = Depends(get_current_user)):
    return {"user_id": session["user_id"]}


def authenticate(email: str, password: str) -> dict | None:
    # Placeholder - real implementation compares against a hashed password
    # (bcrypt/argon2) fetched by email, never plaintext comparison.
    return {"id": 123} if email and password else None
```

## Production Considerations

- **Session stores must be shared across instances.** An in-memory dict works for one process; in production, use Redis or a database so any server behind your load balancer can validate any session.
- **Set a TTL on the session store entry that matches (or slightly exceeds) the cookie's `Max-Age`**, so stale sessions get garbage collected automatically rather than accumulating forever.
- **Rotate session IDs on privilege change** (login, password change, permission elevation) to close the session fixation window.
- **Consider "sliding" vs "absolute" expiration**: sliding expiration extends the session on each activity (better UX, but a stolen cookie stays valid indefinitely with continued use); absolute expiration forces re-authentication after a fixed window regardless of activity (safer for sensitive apps).
- **Sessions vs tokens**: sessions are a strong default for server-rendered apps and first-party web dashboards where the server can hold state and CSRF defenses (SameSite, CSRF tokens) are straightforward to apply. For APIs consumed by mobile apps, third-party integrations, or multiple independent services, stateless [bearer tokens](bearer-tokens.md) usually fit better since they don't require a shared session store across services. Many production systems use both: cookie sessions for the first-party web app, bearer tokens for the public API.

## Common Mistakes

- **Omitting `HttpOnly`**, allowing any injected script (XSS) to read and exfiltrate the session cookie directly.
- **Omitting `Secure`**, letting the cookie be sent over plaintext HTTP where it can be sniffed on shared networks.
- **Not rotating the session ID at login**, leaving the system open to session fixation.
- **Storing sensitive data directly in the cookie** instead of just an opaque session ID — cookies are visible to the client and easy to tamper with unless signed/encrypted, and even then, size limits and unnecessary exposure are downsides.
- **Using a predictable or short session ID** (e.g., an incrementing integer) instead of a long, cryptographically random token — this makes session IDs guessable.
- **Forgetting `SameSite`**, leaving cross-site request forgery easier than necessary.

## Best Practices

- Always set `HttpOnly`, `Secure`, and an appropriate `SameSite` value on authentication cookies.
- Generate session IDs with a cryptographically secure random generator (`secrets.token_urlsafe`, not `random`).
- Store only an opaque ID in the cookie; keep actual session data server-side.
- Rotate the session ID whenever authentication state changes (login, logout-then-login, privilege escalation).
- Give sessions a reasonable absolute expiry even if you also use sliding expiration, so a forgotten logged-in browser doesn't stay valid forever.

## AI Engineering Perspective

Cookie-based sessions are a poor fit for most AI-to-API traffic: LLM backends, agent frameworks, and server-to-server calls to a model provider don't have a browser to store and resend cookies, and they're often stateless or horizontally scaled without a shared session affinity. This is why virtually every LLM provider API (OpenAI, Anthropic, etc.) uses [bearer tokens/API keys](api-keys.md) rather than cookie sessions — see [Part 14 — AI API Engineering](../14-ai-api-engineering/README.md). That said, if you're building the *human-facing* front end of an AI product (a chat UI, an admin console for managing agents), cookie sessions are often still the right choice for that first-party browser session, even while the backend talks to the LLM provider using bearer tokens — the two mechanisms coexist at different layers of the same system.

## Exercises

**Beginner**
1. Explain what problem the `HttpOnly` cookie attribute solves, and what kind of attack it does *not* protect against.
2. Why is it important that logout deletes the session on the server, not just the cookie in the browser?

**Intermediate**
3. Extend the FastAPI example above to reject a session if the client's IP address changes mid-session (a common but imperfect anti-hijacking heuristic) — and explain a legitimate scenario where this would cause a false positive.

**Advanced**
4. Design a session invalidation strategy for a scenario where a user clicks "log out of all devices." What server-side data structure lets you invalidate every session for a user without iterating the entire session store?

## Key Takeaways

- Cookies transport an opaque session ID; the actual session data and its validity live server-side, which is what makes sessions instantly revocable.
- `HttpOnly`, `Secure`, and `SameSite` are not optional extras — they are the core defenses against session theft via XSS, network sniffing, and CSRF respectively.
- Always issue a fresh session ID at login to prevent session fixation; never trust a client-supplied session ID as pre-authenticated.
- Sessions fit server-rendered, first-party web apps well; stateless tokens usually fit APIs, mobile clients, and service-to-service calls better.

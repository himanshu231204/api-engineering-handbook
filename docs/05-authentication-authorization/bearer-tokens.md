# Bearer Tokens

## Why This Matters

Most modern APIs — REST APIs behind mobile apps, service-to-service calls, LLM provider APIs — authenticate requests with a single, unassuming header: `Authorization: Bearer <token>`. Understanding exactly what "bearer" means, and what it implies about trust and risk, is foundational to almost everything else in this Part: [API keys](api-keys.md), [JWTs](jwt-deeply-explained.md), and [OAuth 2.0](oauth2.md) access tokens are all, in practice, bearer tokens. Get the bearer model wrong and you get vulnerable systems that look secure on the surface.

## Core Concept

A **bearer token** is a credential where **possession is proof** — whoever presents ("bears") the token is treated as authorized, with no additional verification of identity. This is codified in [RFC 6750](https://www.rfc-editor.org/rfc/rfc6750) (The OAuth 2.0 Authorization Framework: Bearer Token Usage), which defines the standard `Authorization: Bearer <token>` HTTP header.

The critical implication: **a bearer token is exactly as secure as its transport and storage.** There's no signature tied to the specific request, no proof that the presenter is the original recipient of the token (unlike, say, mutual TLS or DPoP-bound tokens, which cryptographically bind a token to a specific client key). If a bearer token leaks — via a logged header, an XSS attack reading it out of `localStorage`, a man-in-the-middle on plaintext HTTP — the thief can use it exactly as the legitimate holder could, until it expires or is revoked.

## Mental Model

Think of a bearer token like a **concert ticket with no name on it**. Whoever hands the ticket to the usher gets in — the usher doesn't check ID. This is fast and simple (no photo ID check needed at the door), which is exactly why bearer tokens are so widely used for API auth. But it also means: if you drop the ticket and a stranger picks it up, they walk into the concert as you, and there's nothing about the ticket itself that would tip off the usher. The security model depends entirely on *keeping the ticket in your pocket* — not on any property of the ticket.

## How It Works

1. Client obtains a token somehow — via login (receiving a [JWT](jwt-deeply-explained.md) or opaque token), an OAuth flow, or a static [API key](api-keys.md) issued out-of-band.
2. Client attaches it on every request:
   ```
   Authorization: Bearer <token>
   ```
3. Server extracts the token from the header, verifies it (signature check for a JWT, database/cache lookup for an opaque token), and resolves it to a principal and its permissions.
4. No further proof is required — the server does not check that the request came from the same device/client that originally received the token (unless the system layers on additional binding, which most don't).

### Stateless vs stateful bearer tokens

- **Stateful (opaque) tokens**: a random string with no embedded meaning, looked up in a database/cache on every request — same operational shape as an [API key](api-keys.md) or session ID. Instantly revocable (delete the row), but every request costs a lookup, and lookups must be available to every server instance.
- **Stateless (self-contained) tokens**: a [JWT](jwt-deeply-explained.md) that encodes the claims (user ID, expiry, scopes) directly in a cryptographically signed payload. No database lookup needed to verify — the server just checks the signature — which makes stateless tokens attractive for high-throughput, distributed systems. The trade-off, covered in depth in the JWT chapter, is that revocation before natural expiry becomes hard: the token remains "valid" by signature until it expires, even if the server would like to reject it.

This stateless/stateful trade-off is one of the most consequential design decisions in an auth system, and it's why many production systems use a hybrid: short-lived stateless access tokens (limiting the revocation window) paired with a stateful, revocable refresh token — see [Access vs Refresh Tokens](access-vs-refresh-tokens.md).

## Architecture

```mermaid
sequenceDiagram
    participant Client
    participant API as API Server
    participant Verifier as Token Verifier

    Client->>API: GET /v1/resource\nAuthorization: Bearer <token>
    API->>Verifier: Validate token
    alt Stateless (JWT)
        Verifier->>Verifier: Check signature + expiry locally
    else Stateful (opaque)
        Verifier->>Verifier: Look up token in DB/cache
    end
    alt Token invalid, expired, or revoked
        Verifier-->>API: reject
        API-->>Client: 401 Unauthorized
    else Token valid
        Verifier-->>API: principal + claims/scopes
        API-->>Client: 200 OK + resource
    end

    Note over Client,API: Anyone who obtains this exact token string\ncan replay this entire flow successfully.\nThat is the defining property of "bearer".
```

## Request / Response Example

```http
GET /v1/account HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzEyMyIsImV4cCI6MTcyMDAwMDAwMH0.dQw4w9WgXcQ...
Accept: application/json
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{"user_id": "user_123", "plan": "pro"}
```

A missing or malformed `Authorization` header:

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer realm="api", error="invalid_token"
Content-Type: application/json

{"error": "invalid_token", "message": "No bearer token provided"}
```

## Code Example

```python
import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

app = FastAPI()

# FastAPI's HTTPBearer scheme handles extracting the "Authorization: Bearer <token>"
# header for you and raises 403 automatically if the header is missing entirely
# (we still handle "present but invalid" ourselves below).
bearer_scheme = HTTPBearer()

JWT_SIGNING_KEY = os.environ["JWT_SIGNING_KEY"]  # never hardcode secrets
JWT_ALGORITHM = "HS256"


def verify_bearer_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    token = credentials.credentials  # the raw token string, header already stripped
    try:
        # jose.jwt.decode verifies the signature AND standard claims (exp) for us.
        # Explicitly pin the accepted algorithm - never let the token's own
        # header dictate which algorithm to use for verification (see
        # jwt-deeply-explained.md for the "alg: none" attack this prevents).
        payload = jwt.decode(token, JWT_SIGNING_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


@app.get("/v1/account")
async def get_account(claims: dict = Depends(verify_bearer_token)):
    return {"user_id": claims["sub"], "plan": claims.get("plan", "free")}
```

## Production Considerations

- **Always require HTTPS.** Bearer tokens sent over plaintext HTTP can be captured in transit by anyone on the network path; TLS is not optional infrastructure here, it's the primary confidentiality control for the credential itself.
- **Keep bearer tokens out of URLs.** Query strings end up in server logs, browser history, and referrer headers — always use the `Authorization` header, never `?token=...`.
- **Short expiry limits blast radius.** Since possession equals access, a shorter-lived token reduces how long a leaked token remains useful — this is the core motivation for the [access/refresh token pattern](access-vs-refresh-tokens.md).
- **Choose stateful vs stateless deliberately.** If instant revocation (e.g., for compliance, or "kick this compromised session out now") matters more than avoiding a database round-trip, prefer stateful/opaque tokens or a short-lived stateless token plus a revocable refresh token.
- **Consider token binding for high-value systems.** Techniques like DPoP (Demonstrating Proof of Possession) or mutual TLS cryptographically bind a token to the client that requested it, so a bare copy of the token string isn't enough to use it elsewhere — this defeats the "pure bearer" model at the cost of added complexity, and is typically reserved for high-security scenarios.

## Common Mistakes

- **Storing bearer tokens in `localStorage` in browser apps.** Unlike an `HttpOnly` cookie, anything in `localStorage` is readable by any JavaScript running on the page — including injected XSS payloads — making token theft trivial if an XSS vulnerability exists anywhere on the site.
- **Logging the full `Authorization` header.** Application and proxy logs that capture request headers verbatim are a common, accidental leak vector for bearer tokens.
- **Treating a valid bearer token as proof the *original* client is making the request.** Bearer tokens carry no such guarantee — that's the entire point of the "bearer" model — so don't build logic that assumes it.
- **Using overly long expiries "for convenience."** A bearer token valid for 30 days is a 30-day window of full access for anyone who happens to obtain it.
- **Not pinning the verification algorithm** when decoding JWTs used as bearer tokens — see [JWT Deeply Explained](jwt-deeply-explained.md) for the `alg: none` and algorithm-confusion attacks this causes.

## Best Practices

- Transmit bearer tokens only via the `Authorization: Bearer` header, over TLS.
- Prefer short-lived tokens, paired with a separate, revocable refresh mechanism for long sessions.
- If a browser client is involved, prefer storing the token in an `HttpOnly` cookie over `localStorage`/`sessionStorage` where feasible, to reduce XSS exposure.
- Always pin the expected signature algorithm when verifying JWT bearer tokens.
- Never embed bearer tokens in URLs, query parameters, or client-side logs.

## AI Engineering Perspective

Nearly every LLM provider (Anthropic, OpenAI, and most inference platforms) and every internal AI microservice you'll build in [Part 15 — Production AI Systems](../15-production-ai-systems/README.md) uses the bearer scheme — an API key or service token sent as `Authorization: Bearer <key>`. When you build an [LLM gateway](../15-production-ai-systems/README.md) that fronts multiple providers, or a [multi-agent system](../17-ai-agents-and-mcp/README.md) where agents call internal tool APIs, the bearer model's core risk compounds: a leaked bearer token used by an autonomous agent doesn't just expose data to a human attacker, it can be replayed by another automated process indefinitely until caught. This makes short expiry, scope-limiting, and audit logging of bearer token usage especially important in agentic architectures, where the "caller" issuing requests with a given token might not be a human at all, making anomalous usage patterns (unusual request volume, unusual tool calls) one of your few practical detection signals.

## Exercises

**Beginner**
1. In your own words, explain why "bearer" tokens are named that way, and what security property they lack compared to a token cryptographically bound to a specific client.
2. Why should bearer tokens never be passed as a URL query parameter?

**Intermediate**
3. Modify the `verify_bearer_token` dependency above to also check for a required scope claim (e.g., `"scope": "read:account"`) and reject the request with `403` if it's missing, distinct from the `401` for an invalid token.

**Advanced**
4. Compare the operational trade-offs of stateful (opaque, DB-backed) vs stateless (JWT) bearer tokens for a system that needs to support "revoke all sessions for this user immediately" as a security response feature. Which is easier to support, and why?

## Key Takeaways

- A bearer token grants access to whoever presents it — possession alone is proof, with no additional identity check.
- Stateless (JWT) bearer tokens avoid a database lookup per request but are hard to revoke before expiry; stateful (opaque) tokens are instantly revocable but require a lookup.
- Transport security (TLS) and safe client-side storage matter enormously, since a leaked bearer token is immediately usable by whoever has it.
- Short expiry and scope-limiting are the main practical levers for reducing the damage a leaked bearer token can do.

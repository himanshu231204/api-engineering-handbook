# Authentication Methods Cheatsheet

For the full explanation, see [Authentication & Authorization](../../docs/05-authentication-authorization/README.md).

## Quick comparison

| Method | How it works | Stateful? | Best for | Weaknesses |
|---|---|---|---|---|
| **Session + cookie** | Server creates a session on login, stores it (memory/Redis/DB), sends opaque session ID in a cookie | Yes (server-side state) | Traditional server-rendered web apps, first-party browser apps | Doesn't scale horizontally without a shared session store; CSRF risk if not mitigated |
| **API key** | Client sends a static, long-lived secret string (header or query param) | No (usually just a DB lookup) | Server-to-server, third-party integrations, per-project access | No built-in expiry/rotation unless you build it; leaking the key = full access until revoked |
| **Bearer token** | Client sends `Authorization: Bearer <token>`; token could be opaque or a JWT | Depends (opaque = stateful, JWT = stateless) | APIs generally; mobile/SPA clients | Token theft = impersonation until expiry/revocation; must use HTTPS |
| **JWT (as bearer token)** | Self-contained signed token holding claims (user id, roles, expiry) | No (stateless — server just verifies signature) | Distributed systems, microservices, avoiding a shared session store | Can't easily revoke before expiry; token bloat if you cram in too many claims; must protect signing key |
| **OAuth 2.0** | Delegated authorization — a user grants a third-party app scoped access via an authorization server, which issues access/refresh tokens | Depends on token type used underneath | "Login with X", third-party apps acting on a user's behalf, granular scoped access | Complex to implement correctly; several grant types, easy to misconfigure (e.g. implicit flow, missing PKCE) |
| **OpenID Connect (OIDC)** | Identity layer on top of OAuth 2.0 — adds a standardized `id_token` (JWT) proving *who* the user is | No (ID token is stateless) | Single sign-on (SSO), federated identity | Requires understanding it's identity, not authorization — don't use `id_token` as an API access token |

## When to use each

- **Sessions** — you control both frontend and backend, same origin, want easy server-side revocation (logout = delete session).
- **API keys** — machine-to-machine, no human user in the loop, coarse-grained per-client access.
- **Bearer tokens (opaque)** — need instant revocation and a central token store is acceptable.
- **JWT** — need statelessness across many services and can tolerate tokens being valid until they expire (mitigate with short expiry + refresh tokens).
- **OAuth 2.0** — a third party needs limited access to a user's data without ever seeing the user's password.
- **OIDC** — you need "who is this user" (authentication), not just "what can this token do" (authorization) — e.g. building a login system.

## Access vs refresh tokens (quick reference)

- **Access token** — short-lived (minutes), sent on every request, used to authorize API calls.
- **Refresh token** — long-lived (days/weeks), stored securely, exchanged for a new access token when it expires. Never sent on ordinary API calls, only to the token endpoint.
- Rule of thumb: short access token lifetime limits the blast radius of a leaked access token; refresh token rotation limits the blast radius of a leaked refresh token.

## RBAC vs ABAC (quick reference)

| | RBAC (Role-Based) | ABAC (Attribute-Based) |
|---|---|---|
| Decision based on | Role assigned to the user (`admin`, `editor`, `viewer`) | Attributes of user, resource, action, and context (department, resource owner, time of day, IP) |
| Simplicity | Simple to reason about and audit | More flexible, more complex to implement and test |
| Good fit | Small/medium number of clear-cut roles | Fine-grained, contextual, multi-tenant rules |

## Common mistakes

- Storing JWTs in `localStorage` (vulnerable to XSS) instead of an `HttpOnly` cookie.
- Using a JWT as a session replacement but never implementing any revocation strategy (blocklist, short expiry).
- Confusing OAuth (authorization/delegated access) with authentication (who the user is) — use OIDC for the latter.
- Sending API keys in the URL query string (ends up in logs, browser history, proxies).

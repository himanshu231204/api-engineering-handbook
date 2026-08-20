# Authentication vs Authorization

## Why This Matters

Two words that sound similar, get abbreviated the same way in casual conversation ("auth"), and get confused constantly in real codebases — yet they answer completely different questions:

- **Authentication (AuthN)**: *Who are you?*
- **Authorization (AuthZ)**: *What are you allowed to do?*

This isn't a pedantic distinction. A huge share of real-world security incidents — "Insecure Direct Object Reference" bugs, broken function-level access control, privilege escalation — come from engineers building a system that correctly authenticates users but forgets to authorize their actions, or conflates "logged in" with "allowed." If you only remember one idea from this entire Part, make it this: **proving identity and granting permission are two separate steps, and both must happen, in that order, on every protected request.**

## Core Concept

Authentication establishes **identity**. It answers: is this really the user/service/device it claims to be? Mechanisms include passwords, API keys, bearer tokens, mutual TLS certificates, biometrics, magic links — anything that produces a verified claim of "this request comes from principal X."

Authorization establishes **permission**. Given that we know the request comes from principal X, is X allowed to perform this specific action on this specific resource? Mechanisms include role checks (RBAC), attribute checks (ABAC), access control lists, ownership checks ("is this X's own order?"), and scopes on a token.

A system can authenticate perfectly and still have zero authorization logic — every logged-in user can do everything. That's a functioning login system and a completely broken security model at the same time.

## Mental Model

Think of a corporate office building:

- **Authentication is the badge scanner at the front door.** It verifies the badge belongs to a real employee. Once scanned, the door opens — you are "in the building."
- **Authorization is the lock on each individual room.** Being in the building doesn't mean you can walk into the CFO's office or the server room. Each door checks, independently, whether *your specific badge* is cleared for *that specific room*.

A system that authenticates but never re-checks authorization at each door is a building where anyone who gets past the lobby can open every door. This is exactly the bug pattern behind most "any user could view any other user's data by changing the ID in the URL" reports.

## How It Works

A typical protected request flows through both checks, in order:

1. **Extract credentials** from the request — a cookie, an `Authorization: Bearer <token>` header, an API key header.
2. **Authenticate** — verify the credential is valid (signature check, session lookup, password hash comparison) and resolve it to a principal (a user ID, a service account, a client ID).
3. **Authorize** — given the resolved principal, check whether it's permitted to perform *this* operation on *this* resource. This step needs both the principal's permissions (roles, scopes, attributes) and the resource's ownership/sensitivity.
4. **Proceed or reject** — `401 Unauthorized` if authentication failed (we don't know who you are), `403 Forbidden` if authorization failed (we know who you are, and the answer is no).

The 401 vs 403 distinction is the single most common signal that a team understands this split. Returning 401 for "you're logged in but not allowed" is a frequent, telling mistake — see [HTTP status codes](../01-api-foundations/status-codes.md) in Part 1 for the full picture.

## Architecture

```mermaid
sequenceDiagram
    participant Client
    participant API as API Server
    participant AuthN as Authentication Layer
    participant AuthZ as Authorization Layer
    participant DB as Resource Store

    Client->>API: GET /orders/482\n(Authorization: Bearer <token>)
    API->>AuthN: Verify token / session
    alt Invalid or missing credential
        AuthN-->>Client: 401 Unauthorized
    else Valid credential
        AuthN-->>API: principal = user_123
        API->>AuthZ: Can user_123 read order 482?
        AuthZ->>DB: Fetch order 482 owner + policy
        DB-->>AuthZ: owner = user_456, role rules
        alt Not permitted
            AuthZ-->>Client: 403 Forbidden
        else Permitted
            AuthZ-->>API: allow
            API->>DB: Fetch order 482
            DB-->>API: order data
            API-->>Client: 200 OK + order JSON
        end
    end
```

Notice authentication and authorization are drawn as **separate layers with separate failure modes**. Merging them into a single `if user` check is exactly how authorization bugs slip in — "logged in" silently becomes the only check performed.

## Request / Response Example

Authenticated but not authorized — a user tries to read another user's order:

```http
GET /orders/482 HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Accept: application/json
```

```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "error": "forbidden",
  "message": "You do not have permission to access this resource."
}
```

Missing or invalid credential entirely — authentication itself fails:

```http
GET /orders/482 HTTP/1.1
Host: api.example.com
Accept: application/json
```

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer
Content-Type: application/json

{
  "error": "unauthorized",
  "message": "Authentication credentials were missing or invalid."
}
```

## Code Example

```python
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel

app = FastAPI()

# --- Fake data layer for illustration ---
ORDERS = {482: {"id": 482, "owner_id": "user_456", "total": 129.90}}


class Principal(BaseModel):
    user_id: str
    roles: list[str] = []


# --- Step 1: Authentication dependency ---
# Resolves "who is calling?" Raises 401 if the credential is missing/invalid.
def get_current_principal(authorization: str | None = None) -> Principal:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid credential",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.removeprefix("Bearer ")
    # In real code: verify JWT signature/expiry here (see jwt-deeply-explained.md)
    if token != "valid-token-for-user_123":
        raise HTTPException(status_code=401, detail="Invalid token")
    return Principal(user_id="user_123", roles=["customer"])


# --- Step 2: Authorization dependency ---
# Resolves "is this principal allowed to do THIS?" Raises 403 if not.
def authorize_order_access(order_id: int, principal: Principal = Depends(get_current_principal)):
    order = ORDERS.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    is_owner = order["owner_id"] == principal.user_id
    is_admin = "admin" in principal.roles
    if not (is_owner or is_admin):
        # Authenticated successfully, but not permitted -> 403, NOT 401
        raise HTTPException(status_code=403, detail="Not permitted to access this order")
    return order


@app.get("/orders/{order_id}")
async def get_order(order: dict = Depends(authorize_order_access)):
    return order
```

The key structural point: authentication and authorization are **two separate dependencies**, chained. `authorize_order_access` depends on `get_current_principal` but adds its own, resource-specific check. This mirrors the layered architecture diagram above and keeps each concern testable in isolation.

## Production Considerations

- **Authorize per-resource, not just per-endpoint.** Checking "is this user a `customer`?" at the route level is necessary but not sufficient — you still need an ownership/scope check for the *specific record* being accessed (this is the class of bug known as Broken Object Level Authorization, #1 in the OWASP API Security Top 10 — see [Part 10 — API Security](../10-api-security/README.md)).
- **Never derive authorization from client-supplied data.** A `role` field submitted in a request body cannot be trusted; authorization decisions must come from server-side state tied to the authenticated principal.
- **Fail closed.** If the authorization check errors out (database timeout, missing policy), deny the request. Failing open ("if we can't check, let it through") is a common root cause of privilege escalation incidents.
- **Log both 401s and 403s distinctly** — a spike in 403s from one client often signals a misbehaving integration or an attacker probing IDs, while 401 spikes suggest broken token refresh flows or expired credentials.

## Common Mistakes

- **Conflating "logged in" with "allowed."** Checking `if current_user` and then performing any action, with no further permission check, is the single most common source of authorization bugs.
- **Returning 401 when the real answer is 403** (or vice versa). This leaks information incorrectly and confuses client retry logic — a 401 often triggers a token refresh attempt, which will never fix a permissions problem.
- **Trusting client-controlled identifiers for authorization** — e.g. reading a `user_id` from a request body/query string instead of from the verified token/session.
- **Doing authorization once "up front" and reusing the result for multiple resources** in a batch endpoint, instead of checking each resource individually.
- **Skipping authorization on "internal" or admin-only routes** because "no one will guess the URL" — obscurity is not access control.

## Best Practices

- Keep authentication and authorization as **separate, composable layers** (middleware/dependency for authN, per-route or per-resource checks for authZ).
- Centralize authorization logic (a policy function or library) rather than scattering ad hoc `if` checks across route handlers.
- Default to **deny by default**: a resource is inaccessible unless a rule explicitly grants access.
- Write tests that specifically assert **403 for cross-tenant/cross-user access attempts**, not just tests for the happy path.

## AI Engineering Perspective

AI agent systems make this distinction sharper, not softer. An LLM-powered agent might be **authenticated** as a specific user or service account, but the *actions it takes via tool calls* still need per-action authorization — an agent authenticated as a support-bot service account should not automatically be authorized to issue refunds, delete accounts, or read another tenant's data just because the underlying API technically accepts its token. This is central to [Part 17 — AI Agents & MCP](../17-ai-agents-and-mcp/README.md): agent frameworks need explicit authorization guardrails around tool execution, independent of how the agent authenticated to the platform. Treating "the agent has a valid API key" as equivalent to "the agent may do anything" is the agentic-systems version of the classic authN/authZ conflation bug.

For quick definitions of related terms used throughout this Part (principal, claim, scope, and more), see the [glossary](../../resources/glossary.md).

## Exercises

**Beginner**
1. For each of the following, label it authentication or authorization: (a) entering a password, (b) checking if a user's plan includes a feature, (c) scanning a fingerprint, (d) checking if a user owns a document before deleting it.
2. Explain in one sentence why returning `401` instead of `403` for a permission failure is misleading to a client.

**Intermediate**
3. Take the `authorize_order_access` dependency above and extend it so that admins can read any order but only the owner can *delete* one (i.e., different permission rules per HTTP method).

**Advanced**
4. Design (in prose or pseudocode) an authorization check for a multi-tenant SaaS API where a user can belong to multiple organizations with different roles per organization. What information does the authorization layer need beyond the authenticated user ID?

## Key Takeaways

- Authentication answers "who are you?"; authorization answers "what can you do?" — they are distinct steps that both must run.
- Use `401` for failed/missing authentication and `403` for authenticated-but-not-permitted.
- Authorization must be checked per resource/action, not assumed from a general role check at the route level.
- Never trust client-supplied identity or role data for authorization decisions — derive them from the verified credential.
- This split becomes even more important in agentic AI systems, where a valid credential does not imply blanket permission for every tool call.

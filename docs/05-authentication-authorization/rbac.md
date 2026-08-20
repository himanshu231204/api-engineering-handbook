# RBAC

## Why This Matters

Once you've solved authentication — you know *who* is calling, per [Authentication vs Authorization](authentication-vs-authorization.md) — you still need a systematic way to decide *what* they're allowed to do. Checking `if user.email == "admin@company.com"` in scattered `if` statements across a codebase doesn't scale past a handful of routes and is a breeding ground for authorization bugs. **Role-Based Access Control (RBAC)** is the most widely used model for structuring that decision: instead of granting permissions to individuals one by one, you group permissions into **roles**, and assign users to roles. It's the model behind almost every admin panel, cloud IAM system, and multi-user SaaS product you've ever used.

## Core Concept

RBAC has three core building blocks:

- **Permission**: a granular, specific capability — e.g., `orders:read`, `orders:delete`, `invoices:write`.
- **Role**: a named bundle of permissions — e.g., `support_agent` might include `orders:read` and `refunds:create`, while `admin` includes everything.
- **Assignment**: the mapping of users to roles — a user can hold one or more roles, and their effective permissions are the union of every role they hold.

The point of this indirection is **maintainability**: when a new feature needs a new permission, you add it to the relevant role definitions once, and every user with that role automatically gets (or doesn't get) it — you never touch individual user records. Compare this to directly assigning permissions to each user, which becomes an unmanageable, error-prone list as your user base and feature set grow.

## Mental Model

Think of RBAC like **job titles at a company issuing building access badges**. You don't program the door locks with a list of every individual employee's name; you program them with job titles: "Engineering" badges open the server room, "Facilities" badges open the utility closets. When someone is hired as an engineer, you assign them the "Engineering" title, and they instantly inherit all doors that title opens — you never touch the door locks themselves. When the server room's access policy changes, you update it once, for the "Engineering" title, and it applies to every current and future engineer automatically.

## How It Works

1. **Define permissions** — the atomic units of "can do X to Y." Keep them specific and consistently named (`resource:action` is a common convention: `orders:read`, `orders:write`, `orders:delete`).
2. **Define roles** — named groups of permissions, matched to real job functions or user tiers in your product (`viewer`, `editor`, `admin`, `billing_manager`).
3. **Assign roles to users** — typically many-to-many: a user can have multiple roles, and a role can be assigned to many users.
4. **Enforce at request time** — on each request, resolve the authenticated user's roles, compute their effective permission set (the union across all their roles), and check whether the required permission for this action is present.
5. **(Optional) Role hierarchy** — some RBAC systems let roles inherit from other roles (`admin` inherits everything `editor` has, plus more), reducing duplication in role definitions. This adds power but also complexity in reasoning about "what can this role actually do" — use it deliberately, not by default.

### Modeling RBAC in a database

A standard, normalized RBAC schema:

```
users            (id, email, ...)
roles            (id, name)
permissions      (id, name)          -- e.g. "orders:delete"
role_permissions (role_id, permission_id)   -- which permissions a role grants
user_roles       (user_id, role_id)          -- which roles a user holds
```

This many-to-many-via-junction-tables structure is what lets you add a permission to a role without touching every user, and add/remove a user's role without touching permission definitions — the two concerns stay decoupled.

## Architecture

```mermaid
sequenceDiagram
    participant Client
    participant API as API Server
    participant AuthN as AuthN Layer
    participant RBAC as RBAC Enforcement
    participant DB as roles/permissions store

    Client->>API: DELETE /orders/482\nAuthorization: Bearer <token>
    API->>AuthN: Resolve principal
    AuthN-->>API: user_id = 123
    API->>RBAC: Can user_123 perform orders:delete?
    RBAC->>DB: user_roles WHERE user_id=123
    DB-->>RBAC: roles = [support_agent]
    RBAC->>DB: role_permissions WHERE role_id IN (support_agent)
    DB-->>RBAC: permissions = [orders:read, refunds:create]
    RBAC->>RBAC: "orders:delete" not in permission set
    RBAC-->>API: deny
    API-->>Client: 403 Forbidden
```

## Request / Response Example

A role-permitted request:

```http
GET /orders?status=pending HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{"orders": [{"id": 481, "status": "pending"}]}
```

A role-denied request — the caller is authenticated but their role lacks the required permission:

```http
DELETE /orders/482 HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{"error": "insufficient_permissions", "required_permission": "orders:delete"}
```

## Code Example

```python
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

app = FastAPI()


# --- Simulated RBAC data (in production: rows joined from the schema
# described above - roles, permissions, role_permissions, user_roles) ---
ROLE_PERMISSIONS: dict[str, set[str]] = {
    "viewer": {"orders:read"},
    "support_agent": {"orders:read", "refunds:create"},
    "admin": {"orders:read", "orders:write", "orders:delete", "refunds:create"},
}

USER_ROLES: dict[str, list[str]] = {
    "user_123": ["support_agent"],
    "user_456": ["admin"],
}


class Principal(BaseModel):
    user_id: str


def get_current_principal(x_user_id: str) -> Principal:
    # Placeholder for real authentication (see bearer-tokens.md / jwt-deeply-explained.md).
    # In production this comes from a verified token, never a raw header the
    # client can set arbitrarily.
    if x_user_id not in USER_ROLES:
        raise HTTPException(status_code=401, detail="Unknown principal")
    return Principal(user_id=x_user_id)


def get_effective_permissions(principal: Principal) -> set[str]:
    roles = USER_ROLES.get(principal.user_id, [])
    permissions: set[str] = set()
    for role in roles:
        permissions |= ROLE_PERMISSIONS.get(role, set())
    return permissions


def require_permission(permission: str):
    """FastAPI dependency factory: returns a dependency that enforces one permission."""
    def dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
        effective = get_effective_permissions(principal)
        if permission not in effective:
            raise HTTPException(
                status_code=403,
                detail=f"Missing required permission: {permission}",
            )
        return principal
    return dependency


@app.get("/orders")
async def list_orders(principal: Principal = Depends(require_permission("orders:read"))):
    return {"orders": [{"id": 481, "status": "pending"}]}


@app.delete("/orders/{order_id}")
async def delete_order(order_id: int, principal: Principal = Depends(require_permission("orders:delete"))):
    return {"status": "deleted", "order_id": order_id}


@app.post("/orders/{order_id}/refund")
async def refund_order(order_id: int, principal: Principal = Depends(require_permission("refunds:create"))):
    return {"status": "refund_created", "order_id": order_id}
```

Note that `require_permission` is a **dependency factory** — it produces a fresh FastAPI dependency scoped to exactly one permission string, which is then declared per route. This keeps the enforcement logic centralized (one implementation of "check permission") while letting each route declare its own specific requirement, following the layered pattern established in [Authentication vs Authorization](authentication-vs-authorization.md).

## Production Considerations

- **Cache the effective-permissions computation carefully.** Resolving roles → permissions on every request is usually cheap if it's an in-memory join over a small role set, but if role/permission changes need to take effect immediately (e.g., revoking an admin's access right now), avoid caching effective permissions for longer than you're comfortable with a stale grant persisting.
- **Version or audit role/permission changes.** "Who changed this role's permissions, and when" is a question you will eventually need to answer, especially for compliance-sensitive systems.
- **Keep permission names granular and consistent** (`resource:action`) so new endpoints have an obvious permission to require, rather than reusing an overly broad existing one out of convenience.
- **RBAC alone doesn't handle per-resource ownership.** "A support agent can read *any* order" is expressible in RBAC; "a customer can read *only their own* orders" usually needs an additional ownership check layered on top (or a shift toward attribute-based rules — see the planned ABAC chapter in this Part) — RBAC answers "what kind of thing can this role touch," not "which specific instance."
- **Watch for role sprawl.** Systems that create a new one-off role for every slightly different need end up with hundreds of roles that are effectively per-user permission sets again, defeating RBAC's main benefit.

## Common Mistakes

- **Checking roles by name deep in business logic** (`if user.role == "admin"`) scattered across the codebase, instead of centralizing permission checks in one reusable layer — this makes future policy changes error-prone and hard to audit.
- **Conflating RBAC with resource ownership.** Granting `orders:read` at the role level and then forgetting that a "customer" role should only see *their own* orders is a classic Broken Object Level Authorization bug — see [Authentication vs Authorization](authentication-vs-authorization.md) and [Part 10 — API Security](../10-api-security/README.md).
- **Assigning overly broad roles "for convenience"** — giving a support role `orders:delete` because it was easier than adding a narrower permission is exactly how RBAC's least-privilege benefit erodes over time.
- **Trusting a role or permission claim embedded in client-supplied data** rather than resolving it server-side from the authenticated principal.
- **Not testing negative cases** — most test suites verify "admin can delete an order" but skip "support_agent gets 403 trying to delete an order," which is exactly the case most likely to regress silently.

## Best Practices

- Keep permissions granular (`resource:action`) and roles as curated bundles of them, matched to real functional needs.
- Centralize enforcement in one reusable mechanism (a dependency, middleware, or policy library), not scattered inline checks.
- Separate "can this role type do X" (RBAC) from "does this specific resource belong to this user" (ownership/scope checks) — layer both, don't conflate them.
- Write explicit tests for denied cases (wrong role → expect 403), not just allowed ones.
- Periodically audit role definitions for scope creep — a role that's grown to include nearly everything has stopped doing its job.

## AI Engineering Perspective

RBAC extends naturally, and importantly, to AI agents: an agent acting as a service principal should hold its own role(s) with its own scoped permission set, distinct from any human user's roles — an internal "reporting-agent" role might get `analytics:read` and nothing else, structurally preventing it from ever calling a `orders:delete`-gated endpoint regardless of what a crafted prompt tries to get it to do. This is a meaningful defense-in-depth layer for [agent security and guardrails](../17-ai-agents-and-mcp/README.md): prompt injection and jailbreak attempts try to get an agent to *say* it should take an unauthorized action, but if the underlying tool-calling infrastructure enforces RBAC the same way this chapter's `require_permission` dependency does, the enforcement doesn't depend on the model "deciding" correctly — the permission check happens at the API layer regardless of what the model outputs. Treat every tool an agent can call as a route that needs its own permission requirement, exactly like a human-facing API endpoint.

## Exercises

**Beginner**
1. Design three roles (`viewer`, `editor`, `admin`) and their permission sets for a simple blogging API with resources `posts` and `comments`.
2. Explain why RBAC uses a many-to-many relationship between users and roles rather than a single `role` column on the users table.

**Intermediate**
3. Extend the `require_permission` dependency above to support requiring *any one of* several permissions (e.g., a route allowed for either `orders:write` or `orders:admin`).

**Advanced**
4. A support agent should be able to read any customer's orders, but a customer should only read their own. Design how you'd layer an ownership check on top of the RBAC `require_permission` dependency to express both rules without duplicating logic per route.

## Key Takeaways

- RBAC groups permissions into named roles and assigns roles to users, avoiding unmanageable per-user permission lists.
- A normalized schema (users, roles, permissions, and two junction tables) keeps role definitions and user assignments independently maintainable.
- Centralize enforcement in a single reusable mechanism rather than scattering role checks through business logic.
- RBAC answers "what can this role do," not "which specific resource instance can this user touch" — pair it with ownership/scope checks for full authorization coverage.
- Enforcing RBAC at the API/tool-call layer (not relying on model judgment) is an important guardrail for AI agent systems.

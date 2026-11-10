# Multi-Tenant Authorization

> [!TIP]
> **In one line:** In a multi-tenant API the tenant must come from the verified token, flow through a request context, scope every query, and be enforced again by the database.
>
> **In plain English:** An apartment building has one front door and one plumbing system, but your key only opens your flat, and the walls stop you hearing next door. A multi-tenant API shares servers and tables between customers, so it needs "keys and walls" at several levels, not one polite sign.
>
> **You'll be able to:** resolve the tenant from a verified credential instead of request input · scope queries, caches and jobs per tenant · enforce isolation in PostgreSQL with row-level security and prove it with cross-tenant tests

## Why This Matters

Almost every B2B SaaS product is multi-tenant: many customer organisations (tenants) share one deployment, one codebase and often one database. That sharing is what makes the economics work, and it makes one class of bug uniquely catastrophic. A normal authorization bug lets one user see something they shouldn't. A tenant-isolation bug lets *company A read company B's data*: invoices, employee records, customer lists. It ends contracts, triggers breach notifications and regulatory attention, and it is the kind of incident that gets a product written about.

The bug is rarely exotic. It is usually one query that forgot a `WHERE tenant_id = ...`, one endpoint that trusted an `X-Tenant-ID` header, one cache key without a tenant prefix, or one background job that ran with no tenant at all. It is the multi-tenant form of Broken Object Level Authorization (see [Part 10 — API Security](../10-api-security/README.md)), and it persists because correctness depends on every developer remembering a rule on every query, forever. This chapter is about designing so that remembering is not the only line of defence.

Tenant isolation builds on the earlier chapters of this part. [Authentication vs Authorization](authentication-vs-authorization.md) separates "who" from "what may they do", [JWT Deeply Explained](jwt-deeply-explained.md) explains why a verified claim is trustworthy while request input is not, [RBAC](rbac.md) provides roles *within* a tenant, and [ABAC](abac.md) expresses the attribute comparison (`resource.tenant_id == subject.tenant_id`) that tenancy reduces to.

## Core Concept

A **tenant** is the unit of isolation: a customer organisation, workspace or account. Users belong to a tenant (or, in some products, to several). Every piece of tenant-owned data carries a `tenant_id`.

**Isolation models**, from strongest to cheapest:

- **Database per tenant**: strongest isolation, per-tenant backup and restore, awkward at thousands of tenants (connection counts, migrations across N databases).
- **Schema per tenant**: separate namespaces in one database. Moderate isolation, migrations still repeat per schema.
- **Shared tables with a `tenant_id` column** ("pooled"): cheapest and simplest to operate, scales to very many small tenants, and relies entirely on correct scoping. This is the model this chapter focuses on, because it is both the most common and the most demanding.

Many products mix them: pooled tables by default, a dedicated database for a large or regulated customer.

The core rules:

1. **The tenant is an authentication fact, not a request parameter.** It is derived from the verified credential: a claim in a validated JWT (`tid`, `org_id`), or the tenant a verified [API key](api-keys.md) is bound to. It is never read from the URL path, query string, body or an `X-Tenant` header *as an authority*.
2. **Authorization is evaluated inside the tenant.** First "is this resource in my tenant?" (a hard boundary with no exceptions for ordinary users), then "may my role do this?" ([RBAC](rbac.md)) and "do the attributes allow it?" ([ABAC](abac.md)).
3. **Defence in depth.** Scope in application code *and* enforce in the database, so a forgotten filter fails closed.
4. **Everything that holds tenant data is tenant-keyed:** queries, caches, search indexes, object storage paths, queues, logs, metrics labels, files.

## Mental Model

An **office building with a keycard system and a locked floor per company.** You tap your card at the lobby; the card (the verified token) is what decides which floor the elevator takes you to. You can't type a floor number. Inside, each company's filing cabinets are labelled with the company's name (the `tenant_id` column), and the receptionist (your query layer) only fetches files with your company's label. As a final backstop, the filing room itself has a lock that opens only for the label on your card (row-level security), so even a receptionist who makes a mistake cannot hand you another company's folder. The janitor with a master key (support or admin access) exists, but every use is logged, supervised and time-limited.

## How It Works

### 1. Resolve the tenant from the verified token

After signature, issuer, audience and expiry checks, read the tenant claim. If the user can belong to several tenants, the token (or session) is issued *for one* active tenant, and switching tenants means obtaining a new token, which the server checks against membership. If a client does send `X-Tenant-ID` (some APIs expose it for convenience), treat it as a *selector to be verified* against the token's memberships, never as the source of truth. When the header and the token disagree, reject with 403.

### 2. Carry it in a request context

Resolve once, in one dependency or middleware, into an immutable `TenantContext(tenant_id, user_id, roles)`. Handlers and repositories receive the context as an argument. In async Python, per-request values belong in dependencies or `contextvars`, not module-level globals, because many requests interleave on one event loop.

### 3. Scope every query

Every read, update and delete includes the tenant predicate: `WHERE tenant_id = :tenant AND id = :id`. Identifying a row by id alone is the classic leak; ids are not secrets and not unique across tenants in some schemes. Put the predicate in a small repository layer so call sites cannot omit it, and make `tenant_id` part of composite primary or unique keys where uniqueness is per tenant (`UNIQUE (tenant_id, invoice_number)`). Foreign keys should include the tenant too (`FOREIGN KEY (tenant_id, customer_id) REFERENCES customers (tenant_id, id)`), so a row can't point at another tenant's parent.

When a caller asks for another tenant's resource, return **404, not 403**. A 403 confirms the id exists in someone else's data.

### 4. Enforce again in the database: row-level security

PostgreSQL row-level security (RLS) attaches a policy to a table that filters rows for every query, regardless of what the SQL says. The usual pattern is to put the tenant in a transaction-local setting at the start of each request's transaction and write the policy against it. If a developer forgets the filter, the database still returns only the current tenant's rows. If the setting is missing, `current_setting('app.tenant_id', true)` is NULL, the comparison is NULL, and no rows are visible: it fails closed.

Important caveats: RLS does **not** apply to superusers or roles with `BYPASSRLS`, and it does not apply to the table's owner unless you use `ALTER TABLE ... FORCE ROW LEVEL SECURITY`. So the application must connect as a dedicated role that owns nothing, is not a superuser and lacks `BYPASSRLS`, while migrations run as a different role. Use `SET LOCAL` (or `set_config(..., true)`), which lasts for the transaction only; a session-level `SET` would leak the previous tenant into the next request on a pooled connection.

### 5. Make everything else tenant-aware

- **Caches:** prefix every key with the tenant (`t:acme:invoice:9001`). An unprefixed `invoice:9001` key shared across tenants is a leak and a collision.
- **Background jobs and queues:** the job payload carries `tenant_id`, and the worker rebuilds a tenant context (and the RLS setting) before touching data. A job with no tenant should fail, not run unscoped.
- **Search, vector stores, object storage:** include the tenant in index filters, namespaces or key prefixes.
- **Logs and metrics:** tag by tenant for debugging and billing, but keep tenant-supplied data out of metric label cardinality.
- **Rate limits and quotas:** per tenant, not just per IP (see below).

### 6. Admin and support access

Support staff sometimes need to see a tenant's data. Do not give them a "global" role that silently skips scoping. Instead, use explicit impersonation or "act as": the staff member authenticates normally, then obtains a *separate, short-lived* token that names the target tenant and records the actor (for example, `sub` = the support user and an `act` claim identifying the actor, following the OAuth token-exchange pattern). Make it time-boxed, read-only by default, justified by a ticket id, visible in the tenant's audit log, and go through the same scoped code paths as a normal user, so no code path ever needs "if admin, skip the tenant filter".

### 7. Noisy neighbours

Isolation is also about performance. One tenant running a giant export or flooding the API can starve the others. Apply per-tenant rate limits ([Part 6](../06-production-reliability/README.md) covers rate limiting), per-tenant concurrency caps on expensive endpoints, fair scheduling in queues (separate queues or weighted round robin), query timeouts, and connection-pool limits. Large tenants can be moved to dedicated capacity.

### 8. Test isolation explicitly

Write tests that create two tenants with similar data, authenticate as each, and assert that every endpoint, including list, search, export, bulk and nested routes, never returns the other's rows and returns 404 for the other's ids. A generic test can enumerate all routes with an id parameter and attempt cross-tenant access. Also test the database layer directly: with the tenant setting for A, a raw `SELECT *` should see zero rows of B.

## Architecture

```mermaid
flowchart TD
    REQ["Request + Bearer token"] --> V["Verify token\n(signature, iss, aud, exp)"]
    V -->|"tid claim"| CTX["TenantContext\n(one dependency)"]
    HDR["X-Tenant-ID / URL param"] -.->|"never authoritative"| CTX
    CTX --> REPO["Repository layer\nWHERE tenant_id = ctx.tenant_id"]
    CTX --> CACHE["Cache keys\nt:tenant:..."]
    CTX --> JOBS["Job payloads\ntenant_id included"]
    REPO --> TX["Transaction:\nset_config app.tenant_id"]
    TX --> RLS[("PostgreSQL\nRLS policy per table")]
    SUP["Support impersonation token\n(act claim, time-boxed)"] --> V
```

![Four layers keeping tenants apart: the tenant id from a verified token claim, a request context, queries scoped by tenant id, and PostgreSQL row-level security; a worked example shows tenant acme requesting a globex invoice and receiving 404](../assets/diagrams/05-tenant-isolation.svg)

## Request / Response Example

A normal request. The tenant never appears in the request, only in the token. The decoded token payload (after verification) contains `"sub": "u_42"`, `"tid": "acme"`, `"roles": ["billing_manager"]`:

```http
GET /invoices/9001 HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
```

Invoice 9001 belongs to tenant `globex`, so within `acme` it does not exist:

```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{"error": "not_found"}
```

An attempt to override the tenant by header is rejected rather than honoured:

```http
GET /invoices HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
X-Tenant-ID: globex
```

```http
HTTP/1.1 403 Forbidden
Content-Type: application/json

{"error": "tenant_mismatch"}
```

## Code Example

First the database side. The application role cannot bypass RLS, and each policy compares the row's tenant to a transaction-local setting:

```sql
-- Run by the migration/owner role, not the application role.
CREATE TABLE invoices (
    id          bigserial PRIMARY KEY,
    tenant_id   text        NOT NULL,
    number      text        NOT NULL,
    amount_cents bigint     NOT NULL,
    UNIQUE (tenant_id, number)
);
CREATE INDEX ON invoices (tenant_id, id);

ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices FORCE ROW LEVEL SECURITY;  -- applies even to the table owner

CREATE POLICY tenant_isolation ON invoices
    USING      (tenant_id = current_setting('app.tenant_id', true))
    WITH CHECK (tenant_id = current_setting('app.tenant_id', true));

-- The API connects as this role: no ownership, no BYPASSRLS, not a superuser.
CREATE ROLE api_app LOGIN NOBYPASSRLS PASSWORD NULL;  -- set via your secret manager
GRANT SELECT, INSERT, UPDATE, DELETE ON invoices TO api_app;
GRANT USAGE ON SEQUENCE invoices_id_seq TO api_app;
```

Now the FastAPI side: token to context, context to a transaction that sets the tenant, and a repository that scopes explicitly as well (belt and braces):

```python
import os
from dataclasses import dataclass

import jwt  # PyJWT
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import BigInteger, String, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Connect as the restricted role, e.g. postgresql+asyncpg://api_app@db/app
engine = create_async_engine(os.environ["DATABASE_URL"])
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class Invoice(Base):
    __tablename__ = "invoices"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String)
    number: Mapped[str] = mapped_column(String)
    amount_cents: Mapped[int] = mapped_column(BigInteger)


class InvoiceOut(BaseModel):
    id: int
    number: str
    amount_cents: int


@dataclass(frozen=True)
class TenantContext:
    tenant_id: str
    user_id: str
    roles: tuple[str, ...]


def get_tenant_context(authorization: str = Header(...),
                       x_tenant_id: str | None = Header(default=None)) -> TenantContext:
    """The ONLY place a tenant id enters the request. It comes from a verified token."""
    scheme, _, raw = authorization.partition(" ")
    if scheme.lower() != "bearer" or not raw:
        raise HTTPException(401, "Missing bearer token")
    try:
        claims = jwt.decode(
            raw,
            os.environ["JWT_PUBLIC_KEY"],
            algorithms=["RS256"],
            audience=os.environ["API_AUDIENCE"],
            issuer=os.environ["JWT_ISSUER"],
            options={"require": ["exp", "sub", "tid"]},
        )
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid token")
    # A client-supplied tenant header is only a selector we double-check.
    if x_tenant_id is not None and x_tenant_id != claims["tid"]:
        raise HTTPException(403, "tenant_mismatch")
    return TenantContext(claims["tid"], claims["sub"], tuple(claims.get("roles", [])))


async def get_db(ctx: TenantContext = Depends(get_tenant_context)):
    """One transaction per request, with the tenant bound for RLS."""
    async with SessionLocal() as session:
        async with session.begin():
            # is_local=true: the setting lasts only for this transaction, so a
            # pooled connection cannot carry the tenant into the next request.
            await session.execute(
                text("SELECT set_config('app.tenant_id', :t, true)"),
                {"t": ctx.tenant_id},
            )
            yield session


async def get_invoice(db: AsyncSession, ctx: TenantContext, invoice_id: int) -> Invoice | None:
    # Application-level scoping. RLS would filter anyway, but explicit scoping
    # keeps query plans index-friendly and makes intent obvious in review.
    stmt = select(Invoice).where(Invoice.id == invoice_id, Invoice.tenant_id == ctx.tenant_id)
    return (await db.execute(stmt)).scalar_one_or_none()


app = FastAPI()


@app.get("/invoices/{invoice_id}", response_model=InvoiceOut)
async def read_invoice(invoice_id: int,
                       ctx: TenantContext = Depends(get_tenant_context),
                       db: AsyncSession = Depends(get_db)):
    invoice = await get_invoice(db, ctx, invoice_id)
    if invoice is None:
        # Same answer for "does not exist" and "belongs to another tenant".
        raise HTTPException(404, "not_found")
    return invoice


# Tenant-aware cache key: never build keys from the resource id alone.
def cache_key(ctx: TenantContext, kind: str, ident: int | str) -> str:
    return f"t:{ctx.tenant_id}:{kind}:{ident}"
```

A cross-tenant leak test belongs in CI. This one exercises the database layer directly, so it would catch a missing or broken RLS policy even if every code path forgot the filter. `make_session(tenant)` is a fixture that opens a transaction as the restricted role and sets `app.tenant_id` like `get_db` does, and `seed` inserts rows through an owner connection:

```python
import pytest
from sqlalchemy import text


@pytest.mark.asyncio
async def test_rls_hides_other_tenants_rows(seed, make_session):
    await seed("acme", number="INV-1")
    await seed("globex", number="INV-2")

    async with make_session("acme") as db:
        rows = (await db.execute(text("SELECT tenant_id FROM invoices"))).scalars().all()
        assert set(rows) == {"acme"}          # an unfiltered query still sees only acme

        # Writing a row for another tenant must be rejected by WITH CHECK.
        with pytest.raises(Exception):
            await db.execute(text(
                "INSERT INTO invoices (tenant_id, number, amount_cents) "
                "VALUES ('globex', 'INV-X', 1)"))


@pytest.mark.asyncio
async def test_missing_tenant_setting_sees_nothing(seed, make_session):
    await seed("acme", number="INV-1")
    async with make_session(None) as db:       # no app.tenant_id set
        rows = (await db.execute(text("SELECT * FROM invoices"))).all()
        assert rows == []                      # fails closed
```

## Production Considerations

- **Connection pooling.** `SET LOCAL` / `set_config(..., true)` is safe with transaction-level pooling (PgBouncer in transaction mode) because it ends with the transaction. Session-level `SET` is not safe there. Always test with your actual pooler.
- **Performance and indexes.** Lead composite indexes with `tenant_id`. RLS policies add a predicate to every query, so check plans with `EXPLAIN`. Keep policy expressions simple, using plain comparisons rather than function calls the planner can't optimise.
- **Migrations and analytics.** The migration role bypasses RLS by design. Cross-tenant analytics and billing jobs should use a separate, audited role or a replica, never the API's role.
- **Data lifecycle.** Per-tenant export, deletion (including caches, indexes, backups policy) and retention are product requirements. A `tenant_id` on everything makes "delete tenant X" tractable.
- **Tenant-level encryption.** Enterprise customers may require per-tenant keys. Even then, key selection must come from the same trusted context.
- **Observability.** Log the tenant id and actor on every request and every impersonation session. Alert on cross-tenant access attempts (404s caused by tenant mismatch) because a spike is either a bug or an attack.
- **Limits of this approach.** Pooled tables plus RLS isolate *data*, not *resources* or *blast radius*: a bad migration or a bug in shared code affects everyone. Regulated customers may legitimately need a separate database.

## Common Mistakes

- **Trusting `X-Tenant-ID`, a path segment or a body field** as the tenant. Whoever controls the request controls the tenant.
- **Fetching by id alone** (`SELECT ... WHERE id = :id`) and checking the tenant afterwards, or not at all.
- **Cache keys without a tenant**, so one tenant's cached response is served to another.
- **Background jobs without tenant context** that run with a privileged connection and scan everything.
- **Connecting the app as the table owner or a superuser**, so RLS silently doesn't apply, and believing you are protected.
- **Session-level `SET`** on pooled connections, leaking the last tenant into the next request.
- **Returning 403 for another tenant's id**, confirming it exists.
- **A global "admin" role** that bypasses scoping in code, rather than explicit audited impersonation.
- **Skipping list, search, export and aggregate endpoints** when testing isolation. Count and sum endpoints leak too.

## Best Practices

- Derive the tenant from the verified credential in exactly one place, and pass an immutable context everywhere.
- Scope in code and enforce in the database, so a single mistake is not a breach.
- Use a dedicated, non-owner, non-bypass database role for the API, and `FORCE ROW LEVEL SECURITY` where the owner might connect.
- Put `tenant_id` in composite keys, foreign keys, indexes, cache keys, queue messages and storage paths.
- Return 404 for cross-tenant resources and log the attempt.
- Implement support access as time-boxed, audited impersonation through the normal scoped path.
- Run cross-tenant tests in CI for every route, and a database-level RLS test for every table.
- Apply per-tenant rate limits, quotas and concurrency caps.

## AI Engineering Perspective

LLM features multiply the places tenant data can hide, and each needs the same discipline. **Retrieval**: a [RAG](../16-rag-apis/README.md) index must filter by tenant *before* similarity search, using namespaces or a mandatory metadata filter. A retriever that returns the top-k across all tenants and filters afterwards can leak through ranking, caching and logs, and a nearest-neighbour hit from another tenant that reaches the prompt has already leaked. **Caches**: semantic or prompt caches must include the tenant in the key, or one customer's answer is served to another. **Agents**: tools run with the delegating user's tenant context, derived from the verified token, never from arguments the model writes. A prompt-injected "now search tenant globex" should be structurally impossible because the tool has no tenant parameter. See [AI agents and MCP](../17-ai-agents-and-mcp/README.md). **Cost and fairness**: token budgets and rate limits per tenant are the AI form of the noisy-neighbour problem, and per-tenant usage metering is typically needed for billing anyway.

## Exercises

**Beginner**
1. List five places in a typical API (not counting SQL tables) that must carry a tenant identifier to avoid cross-tenant leaks.
2. Why should accessing another tenant's invoice return 404 rather than 403?

**Intermediate**
3. Write the RLS policy and grants for a `customers` table, and explain why the API's database role must not own the table or have `BYPASSRLS`.
4. Write a pytest that logs in as two tenants and checks that `GET /invoices`, `GET /invoices/{id}` and `GET /invoices/export` never return the other tenant's rows.

**Advanced**
5. Design support impersonation: token contents, lifetime, scopes, approval, audit log entries, and how the tenant is notified. What stops a support engineer from using it to read a tenant that never opened a ticket?
6. A single large tenant is hurting latency for others on a shared database. Compare per-tenant rate limits, separate queues, a read replica for that tenant, and moving it to a dedicated database. When does each stop being enough?

## Key Takeaways

- The tenant is a fact from the verified token, not from request input, and it flows through one immutable context.
- Scope every query and tenant-keyed resource, and back it with PostgreSQL row-level security so a forgotten filter fails closed.
- RLS works only if the app role is not the owner, a superuser or `BYPASSRLS`, and the tenant setting is transaction-local.
- Caches, jobs, search and files need tenant keys too. Admin access is audited impersonation, never an unscoped bypass.

### Check Yourself

<details markdown="1">
<summary>1. Where should the tenant id for a request come from, and where must it never come from?</summary>

It comes from the verified credential: a validated token claim, or the tenant bound to a verified API key. It must never be trusted from the URL, query string, body or an `X-Tenant-ID` header, because the caller controls those and could name any tenant.

</details>

<details markdown="1">
<summary>2. If every query already has WHERE tenant_id = :tenant, why add row-level security?</summary>

Application filters depend on every developer remembering them on every query. RLS enforces the same rule inside the database, so a forgotten or buggy filter returns no other-tenant rows instead of leaking them, and a missing tenant setting returns nothing at all.

</details>

<details markdown="1">
<summary>3. You enabled RLS, yet a test shows tenant A reading tenant B's rows. The app connects as the role that created the tables. What is the likely cause and the fix?</summary>

Table owners (and superusers or BYPASSRLS roles) are exempt from RLS unless the table uses FORCE ROW LEVEL SECURITY. Connect the API as a separate role that owns nothing and lacks BYPASSRLS, keep migrations on the owner role, and consider FORCE as a second safeguard.

</details>

---
Back to the [Part 5 README](README.md).

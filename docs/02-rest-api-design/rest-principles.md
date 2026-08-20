# REST Principles

## Why This Matters

Almost every API you'll build or consume in your career calls itself "RESTful." Yet most of these APIs violate at least one of Roy Fielding's original constraints, and that's usually fine. Understanding what REST actually *is* — versus the loose convention the industry settled on — lets you make deliberate design decisions instead of cargo-culting patterns you don't understand. When you know *why* a constraint exists, you know when it's safe to bend it and when bending it will hurt you at scale.

## Core Concept

REST (Representational State Transfer) is an architectural style described by Roy Fielding in his 2000 doctoral dissertation. It's not a protocol, not a standard, and not a library — it's a set of constraints that, when applied to a client-server system built on HTTP, produce APIs with specific desirable properties: scalability, simplicity, and independent evolution of client and server.

Fielding defined six constraints:

1. **Client-server separation** — clients and servers evolve independently, connected only by a uniform interface.
2. **Statelessness** — every request from a client contains all the information needed to process it. The server stores no client session state between requests.
3. **Cacheability** — responses must define themselves as cacheable or not, enabling clients and intermediaries to reuse data.
4. **Uniform interface** — the core REST constraint, broken into four sub-constraints (identification of resources, manipulation through representations, self-descriptive messages, and HATEOAS).
5. **Layered system** — a client can't tell (and shouldn't need to know) whether it's talking directly to the server or through intermediaries like load balancers, gateways, or caches.
6. **Code-on-demand (optional)** — servers can extend client functionality by sending executable code (e.g., JavaScript). Rarely used in API design today.

## Mental Model

Think of REST as "the web, but for machines." A web browser doesn't know in advance every page a website has — it navigates by following links from a starting point, and each page is self-describing (it tells the browser what it is and what you can do next). Fielding's insight was: why not build machine-to-machine APIs the same way? A truly RESTful API would be as discoverable and loosely coupled as a website is to a browser.

In practice, almost nobody builds APIs this way. What the industry calls "REST" is really "HTTP + JSON + resource-shaped URLs" — a pragmatic subset that keeps the parts that are cheap and valuable (statelessness, resource orientation, standard HTTP verbs and status codes) and drops the parts that are expensive and rarely needed (HATEOAS-driven discovery).

## How It Works

**Statelessness in practice**: instead of a server remembering "this client is logged in" via server-side session memory, the client sends an `Authorization` header (a token) with every request. The server validates the token per-request and doesn't need to remember anything about the client between calls. This is why you can put a load balancer in front of ten identical API servers and route each request to a different one — no server needs to "own" a client's session.

**Uniform interface in practice**: resources are identified by URLs (`/orders/123`), manipulated through representations (you `PATCH` a JSON document to change an order, you don't call an RPC method named `updateOrderStatus`), and messages are self-descriptive (the `Content-Type` header tells you it's JSON, the status code tells you what happened).

**HATEOAS — the honest take**: HATEOAS (Hypermedia As The Engine Of Application State) says a response shouldn't just return data — it should return *links* telling the client what it can do next, the same way an HTML page contains `<a>` tags. For example, an order response might include a `cancel` link only if the order is still cancellable. In theory, this means clients don't hardcode business rules like "orders can only be cancelled within 24 hours" — they just check whether the `cancel` link is present.

In practice, the overwhelming majority of production JSON APIs — including ones from Stripe, GitHub, and most companies you've worked with — do not implement HATEOAS. Client SDKs are generated from fixed URL templates and hardcoded knowledge of endpoints. The cost of building and maintaining a truly hypermedia-driven API is high, and the benefit (loose coupling) rarely outweighs the up-front complexity for typical internal or partner APIs. Where HATEOAS *does* show up in real systems, it's usually partial: a `next` link in a paginated list, or a `_links` object for related resources (common in HAL-flavored APIs). Know it exists, know what problem it's solving, but don't feel obligated to build a fully hypermedia-driven API — most teams that try abandon it.

## Architecture

```mermaid
flowchart TD
    A[Client] -->|Stateless request + Auth token| B[Layered System]
    B --> C[Load Balancer]
    C --> D[API Server 1]
    C --> E[API Server 2]
    C --> F[API Server 3]
    D & E & F -->|Uniform interface: URLs + HTTP verbs + JSON| G[(Resource Store)]
    D -.->|Cacheable response headers| H[CDN / Client Cache]
```

Any of the three API servers can handle any request because no server holds client state — that's what makes horizontal scaling trivial.

## Request / Response Example

A stateless, cacheable, resource-oriented request:

```http
GET /orders/5591 HTTP/1.1
Host: api.example.com
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Accept: application/json
```

```http
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: private, max-age=30
ETag: "a1b2c3d4"

{
  "id": 5591,
  "status": "shipped",
  "total_cents": 4999,
  "_links": {
    "self": { "href": "/orders/5591" },
    "invoice": { "href": "/orders/5591/invoice" }
  }
}
```

Notice: the `Authorization` header carries all identity info (statelessness), `Cache-Control`/`ETag` declare cacheability, and `_links` is a lightweight nod to HATEOAS without committing to full hypermedia navigation.

## Code Example

A minimal FastAPI route that demonstrates statelessness — no server-side session, identity comes entirely from the request:

```python
from fastapi import FastAPI, Header, HTTPException

app = FastAPI()

# No session store, no server-side "logged in users" dict.
# Every request must prove who it is via the Authorization header.
def get_current_user(authorization: str = Header(...)) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ")
    # In real code: verify signature/expiry against your auth provider.
    if token != "valid-demo-token":
        raise HTTPException(status_code=401, detail="Invalid token")
    return "user_123"

@app.get("/orders/{order_id}")
def get_order(order_id: int, user_id: str = get_current_user()):
    # This handler can run on ANY server instance — nothing is remembered
    # between requests, so horizontal scaling requires no sticky sessions.
    return {"id": order_id, "owner": user_id, "status": "shipped"}
```

## Production Considerations

- Statelessness has a cost: every request re-authenticates, which means token validation must be fast (favor short-lived signed JWTs over a database lookup per request — see [Part 5](../05-authentication-authorization/README.md)).
- "RESTful" is a spectrum, not a boolean. Most production APIs are "REST-ish": resource URLs, standard verbs, JSON bodies, but no hypermedia. That's a legitimate, deliberate choice — not a failure to implement REST "correctly."
- The layered-system constraint is why API gateways, CDNs, and reverse proxies can sit transparently in front of your service — design your API so it doesn't assume anything about what's between it and the client.
- Full HATEOAS is worth considering when you're building a public API with many independent third-party clients you can't coordinate deploys with — the loose coupling pays off when you can't force everyone to upgrade at once.

## Common Mistakes

- Treating "REST" and "JSON over HTTP" as interchangeable, then being confused when someone points out an API isn't "truly" RESTful.
- Storing session state in server memory (e.g., an in-process dict of logged-in users) and calling the API stateless — this breaks horizontal scaling and sticky-session dependence is a common cause of "works on one server, fails after we added replicas" bugs.
- Trying to force full HATEOAS onto an internal API where every client is a service you control and deploy together — the overhead isn't worth it there.
- Confusing RPC-style endpoints (`POST /createOrder`) with resource-oriented ones (`POST /orders`) and assuming both are "REST."

## Best Practices

- Default to statelessness even if you never touch HATEOAS — it's the constraint with the highest scalability payoff for the least design cost.
- Use standard HTTP semantics (verbs, status codes, caching headers) as your "uniform interface" even in an RPC-ish API — it costs little and every HTTP-aware tool understands it for free.
- Reserve full hypermedia design for genuinely decoupled, long-lived public APIs where clients can't be redeployed on your schedule.
- Be honest in documentation about what level of "RESTful" your API actually implements — it sets correct expectations for integrators.

## AI Engineering Perspective

LLM provider APIs (OpenAI, Anthropic) are a good real-world case study: they're stateless HTTP JSON APIs with resource-shaped endpoints (`/v1/messages`, `/v1/models/{id}`), but they don't implement HATEOAS at all — there's no hypermedia navigation between a chat completion and related resources. That's a deliberate, pragmatic choice: high-throughput, high-frequency APIs prioritize predictable, static endpoint shapes that SDKs can hardcode, over dynamic link-following that would add latency and complexity to every request. When you design your own AI-facing APIs (an LLM gateway, a RAG service — covered in [Part 15](../15-production-ai-systems/README.md) and [Part 16](../16-rag-apis/README.md)), the same trade-off applies: favor statelessness and a uniform interface, and skip HATEOAS unless you have a concrete discoverability problem to solve.

## Exercises

**Beginner**: List the six REST constraints from memory, in your own words, without looking back at this chapter.

**Intermediate**: Take an API you've used recently (GitHub, Stripe, or any public API). Identify which REST constraints it follows and which it skips (especially HATEOAS). Write down evidence for each.

**Advanced**: Design a small resource (e.g., a `/tasks` API) two ways: once with fully hardcoded client-known URLs, and once with `_links` in every response describing available next actions. Compare how much client code changes if the server later renames an endpoint.

## Key Takeaways

- REST is a set of architectural constraints, not a protocol — "RESTful" describes how closely you follow those constraints, not a pass/fail test.
- Statelessness and the uniform interface are the constraints that give REST its biggest practical wins: horizontal scalability and simplicity.
- HATEOAS is the least-adopted constraint in real-world APIs — understand it, use it selectively, but don't treat its absence as a design flaw.
- "REST-ish" JSON-over-HTTP APIs are the industry norm, and that's a legitimate, pragmatic outcome, not a failure to implement REST correctly.

See also: [Resources and Endpoints](resources-and-endpoints.md), [API Contracts](api-contracts.md), and the [glossary](../../resources/glossary.md) for quick definitions of REST-related terms.

# Path Parameters

## Why This Matters

Path parameters are how a URL points at *one specific thing* instead of a category of things. Nearly every non-trivial API operation — fetching a user, updating an order, deleting a comment — needs a way to say "this exact resource, not just resources of this type." Getting path parameter design right (types, validation, structure) prevents an entire class of bugs and security issues, from 404s that should be 400s to accidental data leaks across tenants.

## Core Concept

A **path parameter** is a variable segment of a URL path that identifies a specific resource (or narrows down to a specific sub-collection). In `/orders/482`, `482` is a path parameter representing the order's identifier. In `/orders/482/items/17`, there are two path parameters: the order ID and the item ID.

Path parameters answer "which one?" — as opposed to query parameters, which answer "how should I filter/shape the results?" (see [Query Parameters](query-parameters.md)). The rule of thumb: if removing the parameter would make the URL point at a *different resource*, it's a path parameter. If removing it would just change *how the response looks* (filtered, sorted, paginated), it's a query parameter.

## Mental Model

Think of a path parameter as a placeholder in an address, the way `221B Baker Street` addresses one specific house on Baker Street. The "collection" is the street (`/orders`), and the path parameter is the house number (`482`) — it picks out exactly one address on that street. You can't reach that house any other way; there's no `?house=482` query string version that means the same thing conceptually, because the house number is part of *identifying which resource you mean*, not part of describing what you want to see about it.

## How It Works

Path parameters are declared in route templates using a placeholder syntax (`{order_id}` in OpenAPI/FastAPI, `:orderId` in Express, `<int:order_id>` in Flask). The framework extracts the matching URL segment, converts it to the declared type, and passes it to your handler.

**Type coercion and validation** happen at the routing layer before your business logic runs. If a route declares `{order_id: int}` and a client requests `/orders/abc`, the framework should reject it — ideally with a `404 Not Found` (the resource doesn't exist for that "id") or a `422 Unprocessable Entity` depending on your framework's convention, rather than letting `"abc"` reach your database query as a string and blow up with an opaque 500 error.

**Multiple and nested path parameters** appear when you traverse a resource hierarchy: `/orders/{order_id}/items/{item_id}` requires both IDs to identify the specific item — and critically, your handler should verify that `item_id` actually belongs to `order_id`, not just that `item_id` exists somewhere in the system. Skipping this check is a classic authorization bug (an "insecure direct object reference," IDOR): a client could request `/orders/482/items/999` where item `999` belongs to a completely different order (or a different customer) and get data they shouldn't see.

**Choosing what identifies a resource**: sequential integers (`482`), UUIDs (`550e8400-e29b-41d4-a716-446655440000`), or human-readable slugs (`blue-coffee-mug`) are all valid path parameter values — the choice affects predictability (sequential IDs let attackers guess adjacent resources — enumerate `/orders/1`, `/orders/2`, ...), uniqueness guarantees across distributed systems (UUIDs generate without central coordination), and readability (slugs are nice for public-facing content URLs like `/posts/how-rest-works`).

## Architecture

```mermaid
flowchart LR
    A["Client Request\n/orders/482/items/17"] --> B{Router matches\ntemplate /orders/{order_id}/items/{item_id}}
    B --> C["Extract & type-coerce:\norder_id=482 (int)\nitem_id=17 (int)"]
    C --> D{"Handler: does item 17\nbelong to order 482?"}
    D -->|Yes| E[200 OK + item data]
    D -->|No, belongs elsewhere| F[404 Not Found]
    D -->|order_id doesn't exist| F
```

## Request / Response Example

```http
GET /orders/482/items/17 HTTP/1.1
Host: api.example.com
Accept: application/json
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "id": 17,
  "order_id": 482,
  "sku": "MUG-BLUE-01",
  "quantity": 2
}
```

Requesting an item ID that exists but belongs to a *different* order:

```http
GET /orders/482/items/999 HTTP/1.1
Host: api.example.com
Accept: application/json
```

```http
HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "error": "not_found",
  "message": "Item 999 was not found in order 482"
}
```

Note this returns `404`, not `403 Forbidden` — from this order's perspective, item 999 simply doesn't exist within it, which avoids confirming to a caller whether item 999 exists elsewhere in the system.

## Code Example

```python
from fastapi import APIRouter, HTTPException, Path

router = APIRouter(prefix="/orders")

# Fake data store for demonstration
ITEMS = {
    482: {17: {"id": 17, "sku": "MUG-BLUE-01", "quantity": 2}},
    483: {18: {"id": 18, "sku": "MUG-RED-01", "quantity": 1}},
}

@router.get("/{order_id}/items/{item_id}")
def get_item(
    order_id: int = Path(..., ge=1, description="Order identifier"),
    item_id: int = Path(..., ge=1, description="Item identifier"),
):
    # FastAPI already rejects non-integer path segments with a 422
    # before this function runs, thanks to the `int` type hints.
    order_items = ITEMS.get(order_id)
    if order_items is None:
        raise HTTPException(status_code=404, detail="Order not found")

    item = order_items.get(item_id)
    if item is None:
        # Important: this returns 404 even if item_id exists under a
        # DIFFERENT order — we never leak that fact to the caller.
        raise HTTPException(status_code=404, detail="Item not found in this order")

    return {**item, "order_id": order_id}
```

## Production Considerations

- Always re-validate ownership/scoping for nested path parameters server-side — never assume that because a client supplied `order_id` and `item_id` together, they actually belong together. This is one of the most common real-world API vulnerabilities (OWASP API Security's "Broken Object Level Authorization").
- Decide your ID strategy early and be consistent: sequential integers are easy to read in logs but leak volume information and are guessable; UUIDs avoid that but are harder to type/debug and slightly larger in payloads and indexes.
- Type-coerce and range-validate path parameters (`ge=1` for positive-only IDs) at the framework level so malformed input never reaches your database layer — this closes off a class of injection and crash bugs for free.
- Keep path parameter names consistent across the whole API (`order_id` everywhere, not `orderId` in one route and `id` in another) — inconsistency multiplies client-side mapping code and mistakes.

## Common Mistakes

- Trusting a nested path parameter's relationship without checking it (`/orders/{order_id}/items/{item_id}` fetching `item_id` by itself, ignoring `order_id` entirely) — a serious IDOR vulnerability.
- Returning `500 Internal Server Error` when a path parameter fails to parse (e.g., `/orders/abc`) instead of a clean `404`/`422`.
- Using sequential, predictable IDs for sensitive resources (e.g., `/invoices/1042`) where enumerability itself is a privacy or security risk.
- Overloading a single path parameter to mean different things in different contexts (e.g., `id` sometimes meaning a database primary key and sometimes meaning a public-facing slug).

## Best Practices

- Reserve path parameters strictly for "which resource," never for filtering, sorting, or optional modifiers — those belong in the query string.
- Validate type and format (integer ranges, UUID format) at the routing layer so handlers only ever see well-formed input.
- Always scope nested resource lookups through their full path (query "item 17 where order_id = 482," not just "item 17").
- Choose ID formats deliberately: UUIDs for anything public-facing or security-sensitive; sequential integers are fine for internal, low-sensitivity resources where debuggability matters more.

## AI Engineering Perspective

Path parameters show up constantly in AI APIs: `/threads/{thread_id}/messages/{message_id}` in a conversational agent API, `/files/{file_id}` for an uploaded document in a RAG pipeline, or `/runs/{run_id}` for a specific agent execution. The same IDOR discipline applies with extra weight here — an agent API that fails to verify a `thread_id` belongs to the requesting user could leak another user's entire conversation history, including anything sensitive discussed with the model. Because these systems often use opaque, unguessable IDs (e.g., `run_abc123xyz`, matching how OpenAI and Anthropic format resource IDs) rather than sequential integers, that's also a deliberate mitigation against enumeration attacks on conversation or file data.

## Exercises

**Beginner**: Design the path parameter structure for a bookmarking API with `folders` and `bookmarks` nested inside folders. Write the full URL templates.

**Intermediate**: Given `/customers/{customer_id}/invoices/{invoice_id}`, write pseudocode for the authorization check that must happen before returning invoice data, and explain what status code to return if the check fails.

**Advanced**: Compare sequential integer IDs vs UUIDs vs prefixed opaque IDs (like `inv_8f3d...`) for a public invoicing API. Write a short trade-off analysis covering debuggability, guessability, index performance, and payload size.

## Key Takeaways

- Path parameters identify *which specific resource*; query parameters describe *how to shape the response* — don't mix the two purposes.
- Type-validate and range-check path parameters at the routing layer to fail fast with clean error codes.
- Always verify ownership/scoping for nested path parameters — never trust that two IDs supplied together actually belong together.
- ID format (sequential vs UUID vs opaque prefixed string) is a real security and usability decision, not a cosmetic one.

See also: [Resources and Endpoints](resources-and-endpoints.md), [Query Parameters](query-parameters.md), and [Part 10 — API Security](../10-api-security/README.md) for more on authorization checks.

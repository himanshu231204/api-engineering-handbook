# Python asyncio

## Why This Matters

[Sync vs Async](sync-vs-async.md) established that a synchronous request handler ties up a server resource for the entire duration of any slow work it performs — including I/O that spends most of its time just waiting. `asyncio` is Python's answer to that specific problem: a way to run many I/O-bound operations concurrently on a single thread, so that "waiting" for one operation doesn't block progress on everything else. It's the runtime underneath FastAPI's `async def` routes, `httpx.AsyncClient`, and most modern async database drivers. If you don't understand what asyncio actually does — and, just as importantly, what it *doesn't* do — you will write code that looks async but performs no better than fully synchronous code, or worse, code that silently freezes your entire server under load.

## Core Concept

`asyncio` is Python's library for writing **concurrent** code using `async`/`await` syntax, built around a single-threaded **event loop**. It gives you concurrency without threads or processes — which means no thread-safety issues from shared memory, but also means it only helps when your bottleneck is *waiting on something external* (a network call, a disk read, a database query), not when it's raw CPU computation.

Three building blocks:

- **Coroutine.** A function defined with `async def`. Calling it doesn't run it immediately — it returns a coroutine object that must be `await`-ed or scheduled to actually execute.
- **`await`.** Suspends the current coroutine at that point, handing control back to the event loop, until the awaited operation completes. Crucially, this suspension is *cooperative* — the coroutine chooses to yield control, and only at `await` points.
- **Event loop.** The scheduler that runs coroutines, resumes them when their awaited operation completes, and picks the next ready task to run when one suspends. There's normally one event loop per thread, and in a typical FastAPI app there's exactly one for the whole process.

## Mental Model

Picture a single waiter working a restaurant, instead of the multi-cook kitchen from [Sync vs Async](sync-vs-async.md). The waiter takes an order from table 1, walks it to the kitchen, and rather than standing at the kitchen window waiting for the food, immediately goes to take table 2's order. When the kitchen bell rings for table 1's food, the waiter delivers it — then goes right back to whatever table needed attention next. One person, doing one thing at any given instant, but never standing idle while something else could be progressing.

The waiter can only do this because handing an order to the kitchen is a natural "pause point" — a moment where the waiter isn't needed and can walk away. `await` is exactly that pause point in code: it marks "I've handed this off (to the network, the disk, the database) and I don't need to actively do anything until it comes back." If the waiter instead stood at the kitchen window staring at the pan — the equivalent of calling a blocking, synchronous function from inside a coroutine — every other table starves, no matter how good the underlying kitchen is.

## How It Works

1. You start an event loop (in a FastAPI/Uvicorn app, this happens for you at startup).
2. You schedule coroutines onto it — an incoming HTTP request becomes a coroutine (your `async def` route handler) that the loop runs.
3. Inside that coroutine, when you hit `await some_io_operation()`, control returns to the event loop. The loop is free to run *other* scheduled coroutines — other in-flight requests — while the I/O completes in the background (typically via the operating system's non-blocking I/O primitives, like `epoll` on Linux).
4. When the I/O operation completes, the loop resumes your coroutine exactly where it left off, with the result available.
5. This repeats for every `await` in every coroutine, all interleaved on a single thread, giving the *appearance* of many things happening simultaneously — because from an I/O-wait perspective, they are.

The key mechanical fact: **nothing runs in parallel on multiple CPU cores here.** At any given instant, exactly one coroutine is actively executing Python bytecode; everything else is either finished, waiting on I/O, or waiting for its turn on the loop. This is why asyncio helps I/O-bound work (network calls to an LLM API, database queries, calls to other services) enormously — the "waiting" time overlaps across many operations — but does nothing for CPU-bound work (image processing, heavy computation, parsing huge payloads), where the CPU itself is the bottleneck and there's no idle time to reclaim.

## Architecture

```mermaid
sequenceDiagram
    participant Loop as Event Loop
    participant A as Coroutine A (request 1)
    participant B as Coroutine B (request 2)
    participant DB as Database / LLM API (I/O)

    Loop->>A: run until first await
    A->>DB: await query()
    Note over A: A suspends, control returns to loop
    Loop->>B: run until first await
    B->>DB: await llm_call()
    Note over B: B suspends, control returns to loop
    DB-->>Loop: A's query result ready
    Loop->>A: resume A with result
    A-->>Loop: A completes, response sent
    DB-->>Loop: B's LLM result ready
    Loop->>B: resume B with result
    B-->>Loop: B completes, response sent
```

Both requests are handled on one thread, but because each spends most of its time waiting on external I/O rather than doing CPU work, the loop interleaves them and neither blocks the other — total wall-clock time for both is close to `max(time_A, time_B)`, not `time_A + time_B`.

## Request / Response Example

Consider a FastAPI endpoint that fetches a user's data from a database and simultaneously calls an LLM to summarize their recent activity. Handled well, both I/O operations overlap:

```http
GET /users/42/summary HTTP/1.1
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "user_id": 42,
  "summary": "Active user, 14 orders in the last 30 days...",
  "generated_in_ms": 620
}
```

If the database query takes ~80ms and the LLM call takes ~600ms, and they're run concurrently with `asyncio.gather`, the total is close to 620ms (dominated by the slower call). Run sequentially — even with `await` on each — the total would be closer to 680ms. Run with a *blocking* (non-async) database driver inside an `async def` route, the database call would additionally stall the entire event loop for those 80ms, delaying every other concurrent request on the server, not just this one.

## Code Example

```python
import os
import asyncio
import asyncpg  # async Postgres driver — the sync psycopg2 would block the loop
import httpx
from fastapi import FastAPI

app = FastAPI()

DATABASE_URL = os.environ["DATABASE_URL"]
LLM_API_KEY = os.environ["LLM_API_KEY"]
LLM_ENDPOINT = "https://api.llmprovider.example.com/v1/messages"

# A connection pool is created once at startup and reused across requests —
# creating a new connection per request would itself become a bottleneck.
_pool: asyncpg.Pool | None = None


@app.on_event("startup")
async def startup():
    global _pool
    _pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)


async def fetch_recent_orders(user_id: int) -> list[dict]:
    # await here yields control to the event loop while Postgres processes
    # the query — other requests can run during that wait.
    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT item, created_at FROM orders WHERE user_id = $1 "
            "ORDER BY created_at DESC LIMIT 20",
            user_id,
        )
        return [dict(r) for r in rows]


async def summarize_with_llm(orders: list[dict]) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            LLM_ENDPOINT,
            headers={"Authorization": f"Bearer {LLM_API_KEY}"},
            json={
                "model": "large-model-v2",
                "max_tokens": 150,
                "messages": [{"role": "user", "content": f"Summarize: {orders}"}],
            },
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]


@app.get("/users/{user_id}/summary")
async def user_summary(user_id: int):
    orders = await fetch_recent_orders(user_id)

    # asyncio.gather would let independent awaits run concurrently; here the
    # LLM call depends on `orders`, so it must come after — but if you had
    # two INDEPENDENT slow calls, gather() is how you'd overlap them:
    #   result_a, result_b = await asyncio.gather(call_a(), call_b())
    summary = await summarize_with_llm(orders)

    return {"user_id": user_id, "summary": summary}


# ANTI-PATTERN — do not do this inside an async def route:
# def broken_route():
#     import requests  # sync library
#     resp = requests.get("https://slow-api.example.com")  # BLOCKS the whole
#     # event loop for the full duration of this call — every other request
#     # on this process stalls, not just this one.
```

## Production Considerations

- **A single blocking call inside `async def` stalls every concurrent request on that process**, not just the one making the call — this is far worse than the equivalent mistake in a traditional threaded synchronous server, where at least other threads keep running.
- **CPU-bound work still needs threads or processes.** If you must run something CPU-heavy (image resizing, heavy parsing, cryptographic hashing) inside an async app, offload it with `loop.run_in_executor(...)` (a thread or process pool) rather than awaiting it inline — otherwise it blocks the loop exactly like a blocking I/O call would.
- **Connection pools matter more, not less, in async code.** Because a single process can have many requests in flight concurrently (unlike a thread-per-request model with a hard concurrency ceiling), you need a properly sized async connection pool (database, HTTP client) or you'll exhaust connections under load that a synchronous server might not have reached as quickly.
- **Not every library has an async version.** Popular synchronous libraries (some ORMs, some SDKs) don't have async equivalents; using them inside `async def` reintroduces blocking behavior invisibly.
- **`asyncio.gather` fails fast by default** — if one task raises, the others keep running in the background unless you handle cancellation explicitly; know this before relying on it for critical concurrent operations.

## Common Mistakes

- **Calling a blocking library (`requests`, `psycopg2`, `time.sleep`, synchronous file I/O) inside an `async def` function.** This is the single most common asyncio mistake — it compiles and even works correctly, it just silently kills concurrency, and the bug often isn't visible until production load reveals it.
- **Awaiting things sequentially that could run concurrently.** `result_a = await a(); result_b = await b()` takes `time_a + time_b`; `result_a, result_b = await asyncio.gather(a(), b())` takes closer to `max(time_a, time_b)` when `a` and `b` are independent.
- **Assuming `async` makes CPU-bound code faster.** It doesn't — asyncio provides concurrency for I/O waits, not parallelism for computation. Wrapping a heavy computation in `async def` with no `await` inside it gains you nothing.
- **Mixing sync and async database sessions inconsistently** within the same codebase, leading to confusing bugs about which routes are actually non-blocking.
- **Forgetting to `await` a coroutine call.** `some_async_function()` without `await` just creates a coroutine object and does nothing — Python will usually warn about this ("coroutine was never awaited"), but it's easy to miss in a busy codebase.

## Best Practices

- Use async-native libraries end to end for any I/O in an async route: `asyncpg`/`SQLAlchemy` async engine for Postgres, `httpx.AsyncClient` for HTTP, `redis.asyncio` for Redis.
- Reuse connection pools/clients across requests (create them once at app startup) rather than opening a new connection per request.
- Use `asyncio.gather` (or `asyncio.TaskGroup` in modern Python) to run genuinely independent slow operations concurrently instead of sequentially.
- Push CPU-bound work to a thread/process pool via `run_in_executor`, or better, out of the request path entirely (see [Background Tasks](background-tasks.md)).
- Set explicit timeouts on every `await`-ed I/O call — an async call that never completes still ties up that logical task indefinitely.

## AI Engineering Perspective

Async is close to mandatory for AI-backed APIs. LLM calls (see [Part 14 — AI API Engineering](../14-ai-api-engineering/README.md)) are exactly the kind of I/O-bound, high-latency operation asyncio is designed for — a request that spends 90%+ of its time waiting on the model provider's response, not doing local CPU work. In a synchronous server, one slow LLM call ties up an entire worker; in an async server, that worker's event loop keeps serving other requests while the LLM call is in flight. This becomes essential in RAG pipelines ([Part 16](../16-rag-apis/README.md)), where a single request might need to await an embedding call, a vector database query, and then a generation call — `asyncio.gather` lets you overlap independent steps (e.g., embedding the query while fetching conversation history from your own database) and shrinks total latency. Streaming LLM responses (also Part 14) is itself built on asyncio's ability to yield control between chunks as they arrive, rather than blocking until the full response is generated.

## Exercises

**Beginner**
1. Explain, in your own words, why asyncio helps a route that calls a slow HTTP API but does *not* help a route that resizes a large image in pure Python.
2. Find one blocking call (real or hypothetical) that would be dangerous to leave inside an `async def` route, and describe what would happen to other concurrent requests if it ran under load.

**Intermediate**
3. Rewrite the `user_summary` example so that `fetch_recent_orders` and an independent call (e.g., fetching the user's profile) run concurrently with `asyncio.gather`, instead of sequentially.

**Advanced**
4. Design a strategy for safely calling a CPU-heavy, synchronous-only third-party library (no async version exists) from inside an async FastAPI app, without stalling the event loop. What are the trade-offs of `run_in_executor` vs. moving the work to a separate worker process entirely (see [Background Tasks](background-tasks.md))?

## Key Takeaways

- asyncio provides concurrency on a single thread via an event loop and cooperative suspension at `await` points — it helps I/O-bound work, not CPU-bound work.
- A single blocking (synchronous) call inside an `async def` function stalls the entire event loop, affecting every concurrent request on that process, not just the one making the call.
- Use async-native libraries and connection pools end to end; mixing in synchronous I/O libraries silently defeats the purpose.
- `asyncio.gather` (or `TaskGroup`) lets independent slow operations overlap instead of running sequentially — a direct latency win for multi-step requests like RAG pipelines.
- asyncio is the runtime layer under [Background Tasks](background-tasks.md) and async HTTP/database clients used throughout production AI systems.

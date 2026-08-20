# System Design Interview Questions

System design questions built around Part 19's case studies (`docs/19-system-design-case-studies/`). For the meatier prompts, a full worked answer already exists in the handbook — this file gives you the key points to hit and a pointer to the deep-dive rather than duplicating it.

## How to approach any of these in an interview

Before jumping to any specific question: clarify requirements and scale (functional requirements, read/write ratio, expected QPS, data size), propose a high-level architecture, identify the core data model, dig into 1–2 of the hardest sub-problems in depth, and address failure modes/scaling at the end. Interviewers weight the *process* — how you clarify ambiguity and reason about tradeoffs — more heavily than arriving at one "correct" architecture.

## Warm-up / conceptual

**1. What's the difference between vertical and horizontal scaling, and when does horizontal scaling stop being simple?**
Vertical scaling means a bigger machine (more CPU/RAM); horizontal scaling means more machines. Vertical scaling is simple but hits a hard ceiling and a single point of failure. Horizontal scaling stops being simple once you need shared state — a stateless API server scales horizontally trivially, but the database, session store, and cache behind it need explicit strategies (replication, sharding, a distributed cache) to scale horizontally too.

**2. How do you decide whether a component needs a cache, a queue, or both?**
A cache helps when the same read is requested repeatedly and can tolerate some staleness — it reduces read load and latency. A queue helps when work needs to be decoupled from the request that triggered it (processing can happen later/elsewhere) or when you need to smooth a bursty write/task rate against a fixed processing capacity. Many systems need both: a queue to absorb write/processing bursts, a cache to speed up repeated reads of the processed result.

**3. What's the role of an API Gateway in a system design answer, and when is it worth mentioning?**
Mention it whenever your design has more than a couple of backend services behind a public API — it centralizes auth, rate limiting, TLS termination, and routing so you don't need to justify reinventing those per-service in your answer. It's a reasonable default building block to name early, then move past, rather than a deep area to design in detail unless the question is specifically about it.

## Design an Authentication API

**4. Design an authentication system supporting email/password login, session management, and password reset.**
Key points: hash passwords with a slow, salted algorithm (bcrypt/argon2, never plain MD5/SHA); issue short-lived access tokens + longer-lived refresh tokens (or server-side sessions) after login; rate-limit login attempts to prevent brute force; password reset via a single-use, short-expiry, unguessable token sent to a verified email, never revealing whether an email exists in the system. See `docs/19-system-design-case-studies/design-an-authentication-api.md` for the full worked answer including token rotation and multi-device session handling.

**5. How would you support "log out of all devices" in a JWT-based auth system?**
This is the classic JWT-revocation problem — pure stateless JWTs can't be individually invalidated. Solutions: store a `token_version` (or `valid_after` timestamp) per user, check it on every request against the value embedded/looked-up for that user, and increment it on "log out everywhere" — every previously issued token becomes invalid on its next verification without needing a full token blocklist.

## Design a Payment API

**6. What's the single most important property a payment API must guarantee, and how do you achieve it?**
Idempotency — a network failure must never cause a duplicate charge. Achieve it with a client-generated idempotency key on every charge request; the server stores the key with the result of the first request with that key and returns the same result for retries instead of reprocessing. See `docs/19-system-design-case-studies/design-a-payment-api.md` for the full design including handling partial failures and reconciliation with a payment processor.

**7. How do you handle the fact that a payment provider's webhook confirming a charge might arrive before, after, or never relative to your synchronous API call to charge the card?**
Treat the synchronous charge response as provisional and the webhook as the source of truth for final state — design the order/payment state machine so both the sync response handler and the webhook handler can independently transition state (idempotently) to `confirmed`, and reconcile via a periodic job that queries the provider for any payment stuck in a pending state past a threshold.

## Design a File Upload API

**8. Design an API for uploading large files (multi-GB) reliably.**
Don't proxy the raw bytes through your API server for large files — generate a pre-signed URL to object storage (S3 or similar) and have the client upload directly to it, then notify your API when the upload completes. For very large files, use multipart upload so the client can upload in chunks and resume a failed chunk instead of restarting the whole file. See `docs/19-system-design-case-studies/design-a-file-upload-api.md` for the full design including virus scanning and processing pipelines.

**9. How would you validate an uploaded file's type without trusting the client-provided `Content-Type` header or file extension?**
Inspect the file's actual content — magic bytes/file signature at the start of the file — server-side, since a client can trivially lie about `Content-Type` or rename a file's extension. For anything executed or rendered (images, documents), also run format-specific validation/sanitization, not just a signature check, since a well-formed-looking file can still carry malicious payloads (e.g. polyglot files, embedded scripts in SVGs).

## Design a Webhook System

**10. Design a webhook delivery system (you're the sender) that guarantees at-least-once delivery to customer endpoints.**
Persist every event durably before attempting delivery. Attempt delivery, and on any non-2xx response or timeout, enqueue a retry with exponential backoff, capped at some max duration/attempt count. Sign every payload (HMAC) so customers can verify authenticity. Expose a delivery log/status API so customers can debug missed webhooks. See `docs/19-system-design-case-studies/design-a-webhook-system.md` for the full design including per-customer rate limiting and dead-letter handling.

**11. A customer says they're receiving duplicate webhook events. Is that a bug in your system?**
Not necessarily — at-least-once delivery inherently means duplicates are possible (e.g. your system times out waiting for their `200` even though they did receive and process it, so you retry). This is expected, and the fix belongs on the *consumer* side (see the idempotent consumer checklist in `resources/cheatsheets/webhooks.md`) — every event should carry a unique ID so consumers can deduplicate, and this should be communicated clearly in your API's documentation.

## Design a URL Shortener API

**12. Design a URL shortener: `POST /shorten` returns a short code, `GET /{code}` redirects to the original URL.**
Core design decision is short-code generation: either a counter-based scheme (base62-encode an auto-incrementing ID — guaranteed unique, but predictable/enumerable) or a random-generation scheme (generate random short strings, check for collision, retry — unpredictable, small collision-retry cost). Store the mapping in a fast key-value store; cache hot redirects aggressively since reads (redirects) vastly outnumber writes (shortens). See `docs/19-system-design-case-studies/design-a-url-shortener-api.md` for the full design including analytics and custom aliases.

**13. How would you scale the redirect endpoint to handle very high read QPS?**
Redirects are an ideal caching target — a shortened URL's mapping essentially never changes after creation. Put a cache (Redis, or even a CDN-level edge cache with a short TTL) in front of the database lookup, and consider that `GET /{code}` can often be served from cache alone without touching the origin database for the vast majority of requests.

## Design a Chat API

**14. Design a real-time chat API supporting 1:1 and group messaging.**
Use WebSockets for real-time bidirectional delivery to online users; persist every message to a database regardless of delivery status so history/offline users are covered. Use a message queue or pub/sub layer to fan out a message to all of a user's connected devices/servers, since users in a horizontally-scaled system may be connected to different server instances. See `docs/19-system-design-case-studies/design-a-chat-api.md` for the full design including read receipts, typing indicators, and presence.

**15. How do you guarantee message ordering in a chat system where messages can arrive out of order across servers?**
Assign each message a monotonically increasing sequence number per conversation (not a wall-clock timestamp, which can skew across servers) at write time, and have clients render/sort messages by that sequence number rather than arrival order — this decouples correct ordering from network delivery order.

## Design a RAG API

**16. Design a production RAG API for a company's internal document Q&A.**
Separate the ingestion pipeline (upload → parse → chunk → embed → index, run asynchronously) from the query pipeline (embed query → retrieve → rerank → construct context → generate, run synchronously/streamed). Key production concerns: access control on retrieval (don't return chunks from documents the querying user can't access), citation of sources, and evaluation of retrieval quality separately from generation quality. See `docs/19-system-design-case-studies/design-a-rag-api.md` for the full design.

**17. How would you handle document access control in a multi-tenant RAG system so retrieval never leaks another tenant's data?**
Attach tenant/permission metadata to every chunk at ingestion time, and apply it as a mandatory filter at the vector database query level (not as a post-retrieval filter in application code) — filtering after retrieval risks a chunk being included in a reranking/context step before the permission check happens, and risks the top-K limit being exhausted by chunks the user isn't even allowed to see.

## Design an AI Agent API

**18. Design an API for a coding agent that can read files, run commands, and make edits on a user's behalf.**
Expose the agent as an async task API (`POST /tasks` returns a task ID, work happens in the background, client polls or gets streamed updates) since agent tasks can run long and involve many tool calls. Tool execution needs a sandboxed environment (containerized, not the host machine) with least-privilege access, and destructive actions should be logged and optionally gated behind confirmation. See `docs/19-system-design-case-studies/design-an-ai-agent-api.md` for the full design.

**19. How would you stream an agent's intermediate steps (tool calls, thinking) to a UI in real time, not just the final answer?**
Use Server-Sent Events or a WebSocket connection, emitting a typed event for each step as it happens (`tool_call_started`, `tool_call_result`, `message_delta`, `task_complete`) so the client can render live progress rather than a blank screen until the agent finishes — this is important for agent tasks specifically because they can take much longer than a single LLM call.

## Design an LLM Gateway

**20. Design an LLM gateway that sits in front of multiple LLM providers for your company's internal applications.**
Core responsibilities: unify multiple providers behind one consistent API shape, route requests to the right model/provider (by cost, capability, or explicit client choice), enforce rate limits and track cost/usage per team or application, and provide automatic failover when a provider has an outage. See `docs/19-system-design-case-studies/design-an-llm-gateway.md` for the full design including caching and observability layers.

**21. How do you handle a rate limit hit against a specific provider without failing the client's request?**
Detect the `429` from the provider, and instead of propagating it directly to the client, retry with backoff against the same provider if within budget, or fail over to an alternate provider/model that can serve an equivalent request — the gateway's job is to absorb provider-level rate limiting so it's invisible to internal callers whenever a viable fallback exists.

## Design a Multi-Tenant AI SaaS

**22. Design the backend for a multi-tenant SaaS product that offers an AI-powered feature to each customer.**
Decide on a tenant isolation model up front — shared database with a `tenant_id` column and row-level filtering everywhere (cheaper, simpler ops, higher blast-radius risk of a bug leaking data across tenants) vs. database-per-tenant (stronger isolation, higher operational overhead at scale). Every query, cache key, and vector DB filter must include tenant scoping without exception. See `docs/19-system-design-case-studies/design-a-multi-tenant-ai-saas.md` for the full design including per-tenant rate limits and cost attribution.

**23. How would you prevent one noisy/high-usage tenant from degrading the AI feature's latency for every other tenant?**
Apply per-tenant rate limits and quotas (not just a global limit) at the gateway layer, so one tenant hitting their ceiling gets throttled without affecting others' budget. Consider a bulkhead pattern — isolating resource pools (worker capacity, concurrent LLM requests) per tenant tier so a single tenant's burst can't exhaust a shared pool that every tenant depends on.

## Closing / wrap-up questions

**24. Across all these designs, what's the single most common mistake candidates make in a system design interview?**
Jumping straight to a detailed architecture diagram before clarifying requirements and constraints — scale, read/write ratio, consistency needs, and what "done" looks like for the interview all change the right answer significantly, and skipping that step usually means solving the wrong problem well instead of the right problem adequately.

**25. How do you decide how deep to go on any one sub-component in a 45-minute system design interview?**
Propose the full high-level architecture first so the interviewer can steer you, then let the interviewer's follow-up questions (or your own judgment of which part is most technically interesting/risky) tell you where to go deep — spending all 45 minutes on the data model while never mentioning caching, scaling, or failure handling is a common way to run out of time before covering breadth.

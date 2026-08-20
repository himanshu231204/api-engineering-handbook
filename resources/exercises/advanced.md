# Advanced Exercises

Larger, mini-project-style tasks for readers who've worked through most of the handbook (Parts 11–20), combining distributed systems, observability, and AI/RAG/agent engineering. Expect several hours to a couple of days per exercise.

## 1. Build a 3-provider LLM gateway with circuit breaker + fallback chain
**Relates to:** Part 15 (Multi-Provider Architecture, Fallback Systems), Part 6 (Circuit Breakers)

Build a gateway service that accepts a single chat-completion request and routes it to one of three configurable providers (real providers, or mocked services simulating provider behavior/latency/failures). Wrap each provider call in its own circuit breaker. Implement a fallback chain — if provider A's breaker is open, try B, then C. Write a test that simulates provider A failing consistently (verify the breaker trips and traffic shifts to B), then simulates B also failing (verify traffic shifts to C), and confirms a response is still returned to the caller throughout.

## 2. Implement token-based rate limiting for an LLM proxy
**Relates to:** Part 15 (Token Rate Limits, Cost Tracking)

Build a proxy in front of an LLM API that enforces a token budget per API key (e.g. 100,000 tokens per hour), not just a request-count limit. You'll need to count/estimate input tokens before the call and account for output tokens after the response returns. Persist usage in Redis with a sliding window. Write a test that exhausts a key's budget and confirms subsequent requests are rejected with `429` until the window rolls over.

## 3. Build a production RAG pipeline with access-controlled retrieval
**Relates to:** Part 16 (Document Ingestion, Chunking, Embedding, Vector Databases, Retrieval, Reranking)

Build an end-to-end RAG pipeline: an ingestion endpoint that accepts documents tagged with an owner/tenant ID, a chunking + embedding step (any embedding API/local model), storage in a real vector database, and a query endpoint that retrieves + reranks + constructs context + generates an answer with citations. Critically: enforce that a query from tenant A can never retrieve chunks belonging to tenant B, and write a test that specifically tries to break this isolation.

## 4. Design and implement async document processing with progress reporting
**Relates to:** Part 16 (Async Document Processing), Part 8 (Job Queues, Workers)

Extend the RAG pipeline above so document ingestion is fully asynchronous: upload returns immediately with a job ID, a worker pool processes documents (parse → chunk → embed → index) with retries on transient failures (e.g. embedding API rate limits), and the client can poll or subscribe (SSE/WebSocket) for real-time progress (`parsing`, `chunking`, `embedding: 40%`, `indexed`). Handle the case where a worker crashes mid-job without losing or double-processing the document.

## 5. Build an AI agent with tool calling, a max-iteration guardrail, and audit logging
**Relates to:** Part 17 (Agent Architecture, Agent APIs, Tool Execution, Agent Security and Guardrails)

Build a small agent loop with 3+ real tools (e.g. a calculator, a web search stub, a "read file" tool scoped to a sandboxed directory). Implement a hard cap on loop iterations to prevent infinite loops, classify at least one tool as "destructive" and require an explicit confirmation step before executing it, and log every tool call (name, arguments, result, timestamp) to an append-only audit log. Write a test that deliberately tries to get the agent to loop forever or call the destructive tool without confirmation, and confirms your guardrails hold.

## 6. Build a minimal MCP server and connect it to a real MCP client
**Relates to:** Part 17 (MCP Architecture, MCP Servers, MCP Clients, Tools/Resources/Prompts)

Build an MCP server (stdio or Streamable HTTP transport) exposing at least one tool, one resource, and one prompt for a domain of your choosing (e.g. a server wrapping your notes API from the beginner exercises). Connect it to a real MCP-compatible client/host and demonstrate the model invoking your tool, the host attaching your resource to context, and a user invoking your prompt. Document the exact JSON-RPC messages exchanged for each of the three interactions.

## 7. Implement the Saga pattern for a multi-step order workflow
**Relates to:** Part 11 (Saga Pattern, Monolith vs Microservices)

Model an order workflow as 3 separate "services" (can be separate processes or just clearly separated modules/DBs to simulate the boundary): reserve inventory, charge payment, schedule shipping. Implement it as a saga with compensating actions — if payment fails after inventory was reserved, the saga must release the inventory reservation; if shipping scheduling fails after payment succeeded, the saga must refund the payment and release inventory. Write a test for each failure point that confirms the correct compensating actions run and the system ends in a consistent state.

## 8. Build distributed tracing across 3 services with correlation IDs
**Relates to:** Part 12 (Distributed Tracing, Request IDs, OpenTelemetry)

Build (or simulate) 3 services that call each other in a chain (API gateway → order service → inventory service). Propagate a correlation/request ID through every hop and every log line. Instrument all three with OpenTelemetry and export traces to a local collector (e.g. Jaeger via Docker). Deliberately introduce a slow span in the inventory service and confirm you can identify exactly which service/operation is the bottleneck purely from the trace, without reading logs.

## 9. Implement semantic caching for an LLM-backed endpoint
**Relates to:** Part 15 (Semantic Caching), Part 16 (Embedding APIs)

Build a caching layer in front of an LLM endpoint that, instead of exact-matching the prompt, embeds incoming queries and checks for a cached response from a semantically similar past query (cosine similarity above a threshold) before calling the LLM. Measure your cache hit rate on a test set of paraphrased queries, and write up the tradeoff you observe between your similarity threshold and the risk of returning a wrong cached answer for a query that's similar but not actually asking the same thing.

## 10. Design and load-test a rate limiter comparing two algorithms under bursty traffic
**Relates to:** Part 6 (Rate Limiting), Part 13 (Load Testing)

Implement both a token bucket and a sliding-window-counter rate limiter for the same nominal limit (e.g. 100 requests/minute average). Load-test both with a bursty traffic pattern (e.g. 50 requests in the first second, then quiet) and record how each algorithm handles the burst. Write up which algorithm you'd choose for a public API and why, backed by your test data rather than just the general guidance in the cheatsheet.

## 11. Build a chaos test that kills a dependency mid-request and verify graceful degradation
**Relates to:** Part 6 (Graceful Degradation), Part 13 (Chaos Testing Basics)

Build an endpoint that depends on both a database and a cache, with a fallback path (serve slightly-stale cached data, or a degraded response) if the database is unreachable. Write a chaos test that kills the database connection (or blocks its port) mid-test-run and confirms the endpoint degrades gracefully (returns a `200` with cached/degraded data, or a clear `503`) instead of hanging or crashing. Restore the dependency and confirm the system recovers without a restart.

## 12. Build a complete multi-tenant SaaS backend slice with per-tenant isolation and cost tracking
**Relates to:** Part 18 (Production Architecture), Part 19 (Design a Multi-Tenant AI SaaS), Part 15 (Cost Tracking)

Combine several of the above into one slice of a real product: a multi-tenant API where every request is scoped to a tenant (via API key or JWT claim), an AI feature backed by an LLM call with per-tenant token usage tracked and exposed via a `/usage` endpoint, per-tenant rate limiting so one tenant can't degrade others, and structured logs/traces tagged with `tenant_id` throughout. Write a test that provisions two tenants, exhausts one tenant's rate limit, and confirms the other tenant's requests are completely unaffected.

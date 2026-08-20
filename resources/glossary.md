# Glossary

Alphabetical reference of terms used throughout the handbook. Each entry links to the fuller chapter where one exists.

## A

**ABAC (Attribute-Based Access Control)** — An authorization model that grants or denies access based on attributes of the user, resource, action, and context (e.g. department, resource owner, time of day) rather than a fixed role. More flexible than RBAC but more complex to implement and audit. See [Authentication & Authorization](../docs/05-authentication-authorization/README.md).

**ACID** — The four guarantees a database transaction provides: Atomicity (all-or-nothing), Consistency (valid state to valid state), Isolation (concurrent transactions don't interfere), Durability (committed data survives crashes). See [Databases & APIs](../docs/04-databases-and-apis/README.md).

**Agent Loop** — The iterative cycle an AI agent runs: receive input, let the model decide on an action (respond or call a tool), execute the action, feed the result back into context, repeat until a stop condition is reached. See [Agent Architecture](../docs/17-ai-agents-and-mcp/agent-architecture.md).

**API (Application Programming Interface)** — A defined contract that lets one piece of software request functionality or data from another, without needing to know its internal implementation. See [What is an API?](../docs/00-introduction/what-is-an-api.md).

**API Gateway** — A single entry point that sits in front of one or more backend services, centralizing cross-cutting concerns like authentication, rate limiting, routing, and TLS termination. See [API Gateway](../docs/11-microservices-distributed-systems/api-gateway.md).

## B

**Bulkhead** — A reliability pattern that isolates resources (thread pools, connection pools, worker capacity) into separate compartments, so that one overwhelmed dependency or tenant can't exhaust resources shared by everything else — named after the watertight compartments in a ship's hull. See [Production API Reliability](../docs/06-production-reliability/README.md).

## C

**Cache** — A layer that stores a copy of data so future requests for it can be served faster than recomputing or refetching it from the original source. See [Why Caching Matters](../docs/07-caching-performance/why-caching-matters.md).

**Cache Invalidation** — The process of removing or updating cached data when the underlying source data changes, so the cache doesn't keep serving stale results. Famously one of the two hard problems in computer science. See [Cache Invalidation](../docs/07-caching-performance/cache-invalidation.md).

**Chunking** — Splitting a document into smaller pieces sized appropriately for an embedding model and a retrieval system's context needs, as part of a RAG ingestion pipeline. See [Chunking Pipelines](../docs/16-rag-apis/chunking-pipelines.md).

**Circuit Breaker** — A reliability pattern that wraps calls to a dependency, tracks failures, and "trips" to fail fast (without attempting the call) once failures cross a threshold — protecting both the caller from wasted waiting and the failing dependency from continued load. See [Circuit Breakers](../docs/06-production-reliability/circuit-breakers.md).

**Connection Pooling** — Maintaining a reusable set of open database (or other) connections rather than opening and closing a new connection per request, reducing per-request latency and avoiding exhausting the database's max-connection limit. See [Databases & APIs](../docs/04-databases-and-apis/README.md).

**Context Window** — The maximum number of tokens (input plus output, for most APIs) an LLM can attend to in a single request; exceeding it produces an error rather than silent truncation. See [Context Windows](../docs/14-ai-api-engineering/context-windows.md).

**CORS (Cross-Origin Resource Sharing)** — A browser-enforced mechanism that controls whether JavaScript running on one origin can read the response of a request made to a different origin; it does not prevent the request itself from being sent or processed server-side. See [CORS](../docs/10-api-security/cors.md).

**CSRF (Cross-Site Request Forgery)** — An attack that tricks a logged-in user's browser into submitting a state-changing request to a site using the user's own credentials/cookies, without their intent. Defended against with CSRF tokens and `SameSite` cookies. See [API Security](../docs/10-api-security/README.md).

## D

**Distributed Tracing** — Following a single request's path across multiple services, recording timing and metadata for each hop (span), so you can see exactly where time was spent in a distributed system. See [Distributed Tracing](../docs/12-observability/distributed-tracing.md).

## E

**Embedding** — A numeric vector representation of text (or other data) produced by a model, positioned in a high-dimensional space such that semantically similar inputs produce vectors that are close together — the foundation of vector-based semantic search. See [Embedding APIs](../docs/16-rag-apis/embedding-apis.md).

**Endpoint** — A specific URL (combined with an HTTP method) that a client can send a request to in order to interact with a particular resource or capability of an API. See [Resources and Endpoints](../docs/02-rest-api-design/resources-and-endpoints.md).

**Eventual Consistency** — A consistency model where, after writes stop, all replicas/consumers of the data will eventually converge to the same state, but there's no guarantee of immediate consistency right after a write. Common in distributed and event-driven systems that trade strict consistency for availability/latency. See [Async Systems](../docs/08-async-systems/README.md).

**Event-Driven Architecture** — A system design style where components communicate by producing and consuming events (facts about something that happened) rather than through direct synchronous calls, typically via a message queue or event bus — decoupling producers from consumers in time and knowledge of each other. See [Async Systems](../docs/08-async-systems/README.md).

## F

**Function Calling** — A capability where an LLM, given a set of available functions (name, description, JSON schema for arguments), can output a structured call to one of them instead of free text, which the calling application then executes. Closely related to and often used interchangeably with tool calling. See [Function Calling](../docs/14-ai-api-engineering/function-calling.md).

## G

**gRPC** — A high-performance RPC framework using Protocol Buffers and HTTP/2, offering binary serialization, native streaming, and generated strongly-typed client/server code — commonly used for internal service-to-service communication. See [REST vs gRPC](../docs/11-microservices-distributed-systems/rest-vs-grpc.md).

## H

**HATEOAS (Hypermedia as the Engine of Application State)** — A REST constraint where API responses include links to related actions/resources, so a client can navigate the API dynamically rather than hardcoding URLs — one of the original REST constraints, though rarely fully implemented in practice. See [REST Principles](../docs/02-rest-api-design/rest-principles.md).

## I

**Idempotency** — A property of an operation where performing it once or multiple times produces the same result/end state, making retries safe. `GET`, `PUT`, and `DELETE` are idempotent by definition; `POST` generally is not unless explicitly designed to be (e.g. via an idempotency key). See [Idempotency](../docs/02-rest-api-design/idempotency.md).

**Idempotency Key** — A unique client-generated identifier attached to a request (typically a `POST`) so the server can detect and safely deduplicate retried requests, returning the original result instead of reprocessing. See [Idempotency](../docs/02-rest-api-design/idempotency.md).

## J

**JWT (JSON Web Token)** — A compact, self-contained, signed token format encoding claims (e.g. user ID, roles, expiry) as JSON, verifiable via its signature without a server-side lookup — commonly used as a stateless bearer token for authentication. See [JWT Deeply Explained](../docs/05-authentication-authorization/jwt-deeply-explained.md).

## L

**Latency** — The time it takes for a single request to receive a response, typically measured end-to-end from the client's perspective. See [Latency and Percentiles](../docs/07-caching-performance/latency-and-percentiles.md).

**LLM Gateway** — A service layer that sits in front of one or more LLM providers, unifying their APIs behind a consistent interface and handling cross-cutting concerns like routing, rate limiting, cost tracking, and failover. See [LLM Gateways](../docs/15-production-ai-systems/llm-gateways.md).

## M

**MCP (Model Context Protocol)** — An open protocol standardizing how AI applications (hosts) connect to external tools, data sources, and prompt templates (servers), via a client that maintains the connection — turning bespoke per-integration code into a reusable, interoperable standard. See [MCP Architecture](../docs/17-ai-agents-and-mcp/mcp-architecture.md).

**Message Queue** — A component that decouples producers and consumers of work by holding messages until a consumer is ready to process them, typically delivering each message to exactly one consumer among a pool (competing consumers). See [Message Queues](../docs/08-async-systems/message-queues.md).

**Microservice** — An independently deployable service that owns a specific, bounded piece of business functionality and its own data, communicating with other services over the network (often HTTP or gRPC) rather than in-process function calls. See [Monolith vs Microservices](../docs/11-microservices-distributed-systems/monolith-vs-microservices.md).

## O

**ORM (Object-Relational Mapper)** — A library that maps database rows/tables to objects/classes in application code, letting developers query and manipulate data using the host language's constructs instead of writing raw SQL for every operation. See [Databases & APIs](../docs/04-databases-and-apis/README.md).

**OAuth** — An authorization framework that lets a user grant a third-party application limited, scoped access to their resources on another service, without sharing their password with that application — the basis for "Login with X" and delegated API access flows. See [OAuth 2.0](../docs/05-authentication-authorization/oauth2.md).

**OWASP (Open Worldwide Application Security Project)** — A nonprofit foundation that publishes widely-referenced security guidance, most notably the OWASP API Security Top 10, cataloging the most common and impactful API security risks. See [OWASP API Security](../docs/10-api-security/owasp-api-security.md).

## P

**P95/P99 (Percentile Latency)** — The latency value below which 95% (P95) or 99% (P99) of measured requests fall. Used instead of averages because averages hide tail latency that a meaningful fraction of real users actually experience. See [Latency and Percentiles](../docs/07-caching-performance/latency-and-percentiles.md).

**Prompt Caching** — A provider feature that reuses the processed representation of a repeated prompt prefix (e.g. a system prompt or long document) across requests, reducing cost and latency for the cached portion. See [Prompt Caching](../docs/15-production-ai-systems/prompt-caching.md).

## R

**RAG (Retrieval-Augmented Generation)** — An architecture that retrieves relevant information from an external knowledge source (typically via vector similarity search) and injects it into an LLM's prompt at generation time, grounding the model's response in retrieved facts rather than relying solely on its training data. See [RAG APIs](../docs/16-rag-apis/README.md).

**Rate Limiting** — Restricting the number of requests (or tokens, or other units) a client can make within a given time window, to protect a service from overload or abuse. See [Rate Limiting](../docs/06-production-reliability/rate-limiting.md).

**RBAC (Role-Based Access Control)** — An authorization model that assigns permissions to roles (e.g. `admin`, `editor`, `viewer`) and users to one or more roles, rather than granting permissions to individual users directly. See [RBAC](../docs/05-authentication-authorization/rbac.md).

**Reranking** — A retrieval refinement step that re-scores an initial set of retrieved candidates using a more precise (often slower) model, typically a cross-encoder, to improve the final ranking before the top results are used as context. See [Reranking](../docs/16-rag-apis/reranking.md).

**REST (Representational State Transfer)** — An architectural style for designing networked APIs around stateless requests to named resources, using standard HTTP methods to represent operations on those resources. See [REST Principles](../docs/02-rest-api-design/rest-principles.md).

## S

**Saga Pattern** — A pattern for managing data consistency across multiple services in a distributed transaction, using a sequence of local transactions each paired with a compensating action that undoes it if a later step in the sequence fails. See [Saga Pattern](../docs/11-microservices-distributed-systems/saga-pattern.md).

**Semantic Caching** — Caching LLM responses keyed by the semantic similarity of the query (via embeddings) rather than an exact string match, so differently-worded but similar queries can reuse a cached answer. See [Semantic Caching](../docs/15-production-ai-systems/semantic-caching.md).

**SLA (Service Level Agreement)** — An external, often contractual, commitment made to customers about a service's performance or availability, typically with defined consequences (credits, penalties) for missing it. See [SLI, SLO, SLA](../docs/12-observability/sli-slo-sla.md).

**SLI (Service Level Indicator)** — A quantitative measurement of some aspect of a service's behavior (e.g. request success rate, latency) used as the basis for SLOs and SLAs. See [SLI, SLO, SLA](../docs/12-observability/sli-slo-sla.md).

**SLO (Service Level Objective)** — An internal target value for an SLI (e.g. "99.9% of requests succeed") that a team commits to meeting, generally set with more margin than any external SLA built on top of it. See [SLI, SLO, SLA](../docs/12-observability/sli-slo-sla.md).

**SQL Injection** — A vulnerability where untrusted input is concatenated directly into a SQL query string, letting an attacker inject SQL syntax that changes the query's logic; prevented by using parameterized queries/prepared statements. See [SQL Injection](../docs/10-api-security/sql-injection.md).

**SSE (Server-Sent Events)** — A one-way, HTTP-based streaming protocol where a server pushes a continuous stream of text-formatted events to a client over a single long-lived connection — commonly used for streaming LLM responses and live feeds. See [Server-Sent Events](../docs/09-realtime-and-webhooks/server-sent-events.md).

**Structured Output** — LLM output constrained (typically via a JSON schema) to reliably conform to a specific format, using provider-level enforcement rather than relying on prompt instructions alone. See [Structured Outputs](../docs/14-ai-api-engineering/structured-outputs.md).

## T

**Temperature (Sampling)** — A sampling parameter controlling the randomness of an LLM's next-token selection; low temperature produces more deterministic/focused output, high temperature produces more varied/creative output. See [Temperature and Sampling](../docs/14-ai-api-engineering/temperature-and-sampling.md).

**Throughput** — The rate at which a system processes requests or work over time (e.g. requests per second), as distinct from latency, which measures how long any single request takes. See [Latency and Percentiles](../docs/07-caching-performance/latency-and-percentiles.md).

**Token** — The basic unit an LLM processes text in — a sub-word chunk produced by the model's tokenizer, roughly ¾ of an English word on average; both context window limits and API pricing are measured in tokens. See [Tokens and Tokenization](../docs/14-ai-api-engineering/tokens-and-tokenization.md).

**Tool Calling** — The general term for an LLM's ability to output a structured invocation of an external tool (function, API, action) based on the conversation, which the host application executes and feeds the result back into context — the mechanism underlying most agentic behavior. See [Tool Calling](../docs/14-ai-api-engineering/tool-calling.md).

**TTL (Time To Live)** — The duration a piece of cached (or otherwise temporary) data remains valid before it expires and must be refreshed or refetched. See [Caching & Performance](../docs/07-caching-performance/README.md).

## V

**Vector Database** — A database optimized for storing high-dimensional vectors (embeddings) and performing fast similarity search (typically approximate nearest-neighbor) over them — the retrieval backbone of most RAG systems. See [Vector Database APIs](../docs/16-rag-apis/vector-database-apis.md).

## W

**Webhook** — A server-to-server callback: instead of a client polling for updates, the sending service makes an HTTP request to a URL the receiver has registered in advance whenever a relevant event occurs. See [Webhooks](../docs/09-realtime-and-webhooks/webhooks.md).

**WebSocket** — A protocol providing a persistent, full-duplex connection between client and server over a single TCP connection, allowing both sides to send messages at any time — used for real-time, bidirectional communication like chat. See [WebSocket](../docs/09-realtime-and-webhooks/websocket.md).

## X

**XSS (Cross-Site Scripting)** — A vulnerability where untrusted input is rendered into a page without proper escaping, letting an attacker inject and execute malicious JavaScript in another user's browser session. See [API Security](../docs/10-api-security/README.md).

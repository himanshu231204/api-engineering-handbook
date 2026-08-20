# Software Engineer Interview Questions

Broader software-engineering questions spanning API foundations, security, async systems, and microservices — useful for general SWE interviews where APIs are one part of a wider role.

## Fundamentals

**1. What actually happens between typing a URL and seeing a webpage load?**
DNS resolves the domain to an IP address, the browser opens a TCP connection (with a TLS handshake if HTTPS), sends an HTTP request, the server processes it and sends back an HTTP response, and the browser parses/renders the response (HTML, then fetching linked assets). Interviewers are listening for whether you know DNS, TCP/TLS, and HTTP are distinct layered steps, not one opaque "the internet."

**2. What's the difference between HTTP and HTTPS, mechanically?**
HTTPS is HTTP layered over TLS. TLS adds a handshake that establishes an encrypted channel (using asymmetric crypto to exchange a shared symmetric key) and verifies the server's identity via a certificate signed by a trusted CA. Everything after the handshake — headers, body — is encrypted in transit, unlike plain HTTP.

**3. Explain how JSON serialization can silently lose or change information, with an example.**
JSON has no native `Date`, `Set`, or arbitrary-precision-integer/`Decimal` type — dates get serialized to strings (and must be parsed back with an agreed format), very large integers can lose precision in languages that parse JSON numbers as floats (e.g. JavaScript), and key order isn't guaranteed to be preserved by every parser. Contracts need to be explicit about formats (e.g. ISO 8601 for dates) rather than relying on JSON's native types.

**4. What's a race condition, and can you give an API-relevant example?**
A race condition happens when the correctness of a result depends on timing/ordering of concurrent operations. Example: two concurrent `PATCH` requests both read a resource's current value, each computes an update based on that stale read, and the second write silently clobbers the first's change. Fixes include optimistic locking (version field, fail on mismatch), database-level atomic operations, or pessimistic locking (row locks) for high-contention cases.

## Async & Concurrency

**5. What's the difference between concurrency and parallelism?**
Concurrency is structuring a program to handle multiple tasks by interleaving their progress (not necessarily simultaneously) — useful for I/O-bound work where tasks spend most of their time waiting. Parallelism is literally executing multiple tasks at the same instant on multiple cores — useful for CPU-bound work. Python's `asyncio` gives concurrency (via an event loop and cooperative yielding on I/O), not parallelism, within a single process.

**6. When would you reach for `asyncio` versus a thread pool versus a process pool in Python?**
`asyncio` for I/O-bound work where you control the code doing the waiting (network calls, DB queries) and can use async-native libraries. A thread pool for I/O-bound work with blocking libraries you can't rewrite as async (still benefits because Python releases the GIL during I/O). A process pool for CPU-bound work, since the GIL prevents true parallel CPU work across threads in a single process.

**7. What's a background task, and when should work move from a request handler into one?**
A background task runs outside the request/response cycle — the API responds immediately while the actual work (sending an email, processing an upload, generating a report) happens asynchronously, often via a job queue and worker process. Move work to the background whenever it's slow, unreliable, or not needed to form the immediate response — this keeps API latency low and lets you retry failed work independently of the original request.

**8. What's the difference between a message queue and a pub/sub system, conceptually?**
A queue typically delivers each message to exactly one consumer (competing consumers, good for distributing work). Pub/sub broadcasts each message to every subscriber of a topic (good for fan-out, notifying multiple independent systems of an event). Some systems (like Kafka) blur this line by supporting both patterns depending on consumer group configuration.

**9. What is eventual consistency, and why would a system choose it deliberately?**
Eventual consistency means that after writes stop, all replicas/consumers will *eventually* converge to the same state, but there's no guarantee of immediate consistency after a write. Systems choose it deliberately to gain availability and partition tolerance (per CAP theorem) or lower latency, when the domain can tolerate a brief window of staleness (e.g. "likes" count, search index updates) in exchange for not blocking writes on full synchronous replication.

## Security

**10. What is a CSRF attack, and how do you defend against it?**
Cross-Site Request Forgery tricks a logged-in user's browser into submitting a request to your site (e.g. a form auto-submitting to `POST /transfer-funds`) using the user's own cookies, without their intent. Defenses: CSRF tokens (a per-session/per-form secret the attacker's page can't know), `SameSite=Strict`/`Lax` cookies, and checking the `Origin`/`Referer` header on state-changing requests.

**11. How does SQL injection happen, and why does parameterized querying fix it?**
It happens when user input is concatenated directly into a SQL string, letting an attacker inject SQL syntax (e.g. `' OR '1'='1`) that changes the query's logic. Parameterized queries (prepared statements) send the query structure and the user's values separately to the database driver, so user input is always treated as data, never as executable SQL, regardless of its content.

**12. What's reflected XSS vs stored XSS?**
Reflected XSS: malicious script is part of the request (e.g. a query parameter) and gets echoed back unescaped in the response, executing in the victim's browser — requires tricking the victim into clicking a crafted link. Stored XSS: the malicious script is saved server-side (e.g. in a comment field) and served to every user who views that content, no crafted link needed — generally more dangerous due to wider reach.

**13. Where should secrets (API keys, DB passwords) live, and what's wrong with putting them in source code?**
Secrets belong in a secrets manager, environment variables injected at deploy time, or a vault service — never committed to source control, where they persist in history forever even if later removed, and become visible to anyone with repo access (including in public repos, to the whole internet). Rotate any secret that was ever committed, don't just remove it from the latest commit.

**14. What does CORS actually protect against, and what does it not protect against?**
CORS is a browser-enforced mechanism that restricts which origins can read the response of a cross-origin request made from JavaScript in the browser. It does *not* prevent the request from being sent (the server still receives and can act on it) — it only controls whether the browser lets the calling page's JavaScript read the response. It's not a server-side security control and does nothing for non-browser clients (curl, mobile apps, server-to-server).

## Microservices & Distributed Systems

**15. When would you split a monolith into microservices, and what's the cost of doing it too early?**
Split when independent teams need to deploy independently, when parts of the system have wildly different scaling needs, or when a bounded context has become large/complex enough to warrant its own lifecycle. Splitting too early adds distributed-systems complexity (network calls instead of function calls, partial failure, data consistency across services, operational overhead) before the team has enough scale or organizational need to justify it — "premature microservices" is a well-known anti-pattern.

**16. REST vs gRPC — when would you pick each?**
REST/JSON over HTTP is human-readable, universally supported (including browsers), and simple to debug — good for public APIs and browser clients. gRPC (Protocol Buffers over HTTP/2) is more efficient (binary, smaller payloads), supports streaming natively, and generates strongly-typed client/server code — good for internal service-to-service communication where both ends are under your control and performance matters.

**17. What problem does an API Gateway solve in a microservices architecture?**
It gives external clients a single entry point instead of talking to N services directly, and centralizes cross-cutting concerns — auth, rate limiting, request routing, logging, TLS termination — so individual services don't each reimplement them. It also decouples the external API surface from internal service boundaries, so you can refactor services without breaking clients.

**18. What is the Saga pattern, and why do distributed systems need it?**
A saga is a sequence of local transactions across multiple services, each with a defined compensating action to undo it if a later step fails — used because distributed transactions (a single ACID transaction spanning multiple databases/services) don't scale well and most systems avoid them. If step 3 of 5 fails, the saga runs compensating actions for steps 2 and 1 to bring the overall system back to a consistent state.

## Observability & Debugging

**19. A service's error rate spiked after a deploy. Walk through how you'd investigate.**
Check the deploy timeline against the error spike to confirm correlation. Look at error logs/traces for the specific error signature (stack trace, error type). Check whether it's isolated to one endpoint/dependency or systemic. Compare metrics (latency, error rate, resource usage) before/after the deploy. If the deploy is the clear cause, roll back first to restore service, then investigate the root cause with the rollback buying time.

**20. What's a request ID / correlation ID, and why does it matter in a distributed system?**
A unique ID generated at the edge (or by the client) and propagated through every downstream service call for a single logical request, included in every log line and trace span. It lets you reconstruct the full path of one request across many services from logs/traces alone, which is otherwise nearly impossible once a request fans out across a microservices architecture.

**21. What's the difference between SLI, SLO, and SLA?**
SLI (Service Level Indicator) is a measured metric (e.g. "99.95% of requests succeeded in the last 30 days"). SLO (Service Level Objective) is your internal target for that metric (e.g. "99.9% success rate"). SLA (Service Level Agreement) is an external, often contractual, commitment to customers with consequences (credits, penalties) for missing it — typically set looser than your internal SLO to leave margin.

## Testing & CI/CD

**22. What is contract testing, and what problem does it solve that integration testing doesn't?**
Contract testing verifies that a service's API matches what its consumers expect, without spinning up the full dependency graph — a consumer defines expectations (a "pact"), and the provider is tested against them independently. It catches breaking API changes between independently-deployed services faster and more cheaply than full integration/E2E tests, which require the whole stack running together.

**23. How would you design a CI pipeline for an API service?**
Run linting and unit tests on every push (fast feedback). Run integration tests against a real (containerized) database in CI. Build the artifact/image. Run contract tests against dependent/dependency services if applicable. Deploy to a staging environment and run smoke/E2E tests. Gate production deploys on all of the above passing, ideally with automated rollback on post-deploy health check failures.

**24. Why use a real (containerized) test database instead of mocking the database layer entirely?**
Mocking the DB layer means your tests never exercise real SQL, constraints, transactions, or ORM query-generation behavior — bugs there (a bad JOIN, a missing index causing an N+1, a broken migration) go undetected until production. A containerized test DB (e.g. via Testcontainers or Docker Compose) gives realistic coverage at a manageable speed/cost tradeoff versus testing against a shared/hosted environment.

**25. What's the difference between load testing and stress testing?**
Load testing measures how the system behaves under expected/peak realistic traffic, to validate it meets performance targets (latency, throughput) at that load. Stress testing pushes beyond expected limits deliberately, to find the breaking point and observe *how* the system fails (gracefully with backpressure/errors, or catastrophically) — used to find capacity ceilings and failure modes before they're discovered in production.

# Changelog

All notable changes to this project are documented here. Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added

- **The last 50 chapters** — every 🚧 Planned chapter in Parts 5–13 and 18 is now written, so all 20 parts (192 chapters) are complete: OpenID Connect, ABAC and multi-tenant authorization (Part 5); jitter, idempotency in practice, bulkheads, graceful degradation, health checks and probes (Part 6); write-through caching, TTL, distributed caching, CDN basics and performance bottlenecks (Part 7); job queues, workers, RabbitMQ, Kafka, event-driven architecture and eventual consistency (Part 8); long polling, streaming APIs, event ordering and duplicate events (Part 9); CSRF, XSS, abuse protection and webhook security (Part 10); service discovery, load balancing, service-to-service auth, Protocol Buffers, distributed transactions and event-driven microservices (Part 11); structured logging, tracing, request IDs, OpenTelemetry, error monitoring and debugging production APIs (Part 12); end-to-end, contract, stress and chaos testing, API mocking, test databases and CI/CD pipelines (Part 13); security, observability and cost management in production (Part 18). Each has a TL;DR, a Check Yourself quiz and a Mermaid diagram; 20 new SVG diagrams.
- Older chapters that called these topics "planned" or "upcoming" now link to them.
- **Readability pass:** every written chapter now opens with a TL;DR callout ("In one line" / "In plain English" / "You'll be able to") and ends with a 3-question **Check Yourself** quiz with hidden answers.
- **Hand-drawn SVG concept diagrams** in `docs/assets/diagrams/` (HTTP anatomy, DNS, TLS, JWT, OAuth 2.0, circuit breaker, token bucket, cache-aside, queues, webhooks, tokenization, RAG pipeline, agent loop, MCP and more), embedded in their chapters and collected on the site's Diagrams page.
- **Redesigned GitHub Pages site:** full chapter navigation in the sidebar, generated from the part status tables; four learning tracks as top tabs; prev/next links; "Part N · Chapter k of M" crumbs; progress bars on part pages; fixed brand colours and dark-mode contrast; new home page with a learning-path diagram.
- `docs/study-plan.md` (three week-by-week tracks) and a browser-saved Progress Tracker page.
- `scripts/check_svgs.py`, `scripts/check_chapters.py` (template, TL;DR and quiz conventions for every chapter) and a strict `mkdocs build` job in CI.
- `CLAUDE.md` and `AGENTS.md` — conventions for AI coding agents working in this repo (chapter template, status model, cross-linking rules, verification scripts).
- `.github/workflows/ci.yml` — link check + examples compile check on every push/PR, plus an advisory markdownlint pass.
- `scripts/check_links.py` and `scripts/check_examples_compile.py`.
- `.github/PULL_REQUEST_TEMPLATE.md` and `.github/ISSUE_TEMPLATE/` (bug report, chapter request).
- Repository scaffold: full `docs/` structure for all 20 parts plus introduction, `examples/`, `diagrams/`, `projects/`, and `resources/`.
- Root documentation: `README.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `ROADMAP.md`, `LICENSE`.
- Part index pages (`README.md`) for all 20 parts with chapter lists, prerequisites, and status tracking.
- Core architecture diagrams in `diagrams/`.
- Cheatsheets, glossary, interview question sets, and exercises in `resources/`.
- Capstone project specifications in `projects/01`–`projects/10`.
- 12 runnable code examples in `examples/`.
- 10 fully worked system design case studies in `docs/19-system-design-case-studies/`.
- Reference implementations (FastAPI + Pydantic v2 + SQLAlchemy async + SQLite) for capstone projects 01 (Bookshelf CRUD API), 02 (Authentication Service), and 04 (Webhook Processing System), each with `app/`, `tests/`, `requirements.txt`, `.env.example`, and a "Reference Implementation" section on its `README.md` — satisfies the v0.7 milestone.

### Fixed
- **26 Mermaid diagrams that did not render** on GitHub and the Pages site: unquoted flowchart labels containing parentheses or braces (9 capstone project specs and 3 chapters), `;` inside sequence-diagram messages, a `Loop` participant that collided with Mermaid's `loop` keyword, the unsupported `-.x` edge, an edge to a spaced subgraph name, and `\n` printed literally in sequence/state diagrams (now `<br/>`). All 172 diagrams were validated against mermaid@11.
- Corrected README status tables for Parts 5–13 and 18: flipped 50 chapters from ✅ Written back to 🚧 Planned where the chapter files don't exist on disk; `scripts/check_links.py` reports 0 broken links in `docs/`.

## [0.1.0] — Initial scaffold
- Project initialized.

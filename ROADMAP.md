# Roadmap

This handbook is built incrementally, prioritizing depth over speed. This page tracks the overall build plan. For chapter-level status, see each part's `README.md`.

## Philosophy

> "No empty placeholder chapters unless explicitly marked as planned."

Every part has a complete index page describing exactly what it will cover, even before every chapter is written. Chapters are filled in part-by-part, prioritizing:

1. Foundational parts (1–3) — required to understand everything after them.
2. AI API engineering parts (14–17) — the handbook's primary differentiator.
3. Production concerns (4–13) — reliability, security, observability, testing.
4. Capstones (18–20) — architecture, case studies, and projects that tie everything together.

## Milestones

- [x] **v0.1 — Repository scaffold.** Full directory structure, root files, all 20 part indexes with chapter lists and status tables.
- [x] **v0.2 — Core foundations.** Parts 1–3 (API Foundations, REST Design, Building APIs with FastAPI) written in full.
- [x] **v0.3 — AI API engineering core.** Parts 14–17 (LLM APIs, Production AI Systems, RAG APIs, AI Agents & MCP) written in full.
- [x] **v0.4a — Databases.** Part 4 (Databases & APIs) written in full.
- [x] **v0.4 — Backend production skills.** Parts 5–10 (Auth, Reliability, Caching, Async, Realtime, Security) written in full.
- [x] **v0.5 — Distributed systems & operations.** Parts 11–13 (Microservices, Observability, Testing) written in full.
- [x] **v0.6 — Synthesis.** Parts 18–19 (Production Architecture, System Design Case Studies) written in full.
- [x] **v0.9 — All 190 chapters written.** Every part's status table is 100% ✅ Written, 0 broken internal links across the repo (`scripts/check_links.py`).
- [ ] **v0.7 — Capstone reference implementations.** All 10 capstone projects are fully specified (done); reference implementations for at least 3 projects beyond the spec stage.
- [ ] **v0.8 — Examples hardening.** All 12 `examples/` directories live-tested end to end with real dependencies installed (several are currently syntax-verified but not fully runtime-tested — see each example's README for its verification status).
- [ ] **v1.0 — Polish pass.** Full read-through for tone/terminology consistency across all 20 parts, glossary cross-reference audit, and a pass to replace any illustrative pseudo-SDK code with real, currently-correct provider SDK calls where a stable public API exists.

## How Contributions Fit In

Community contributions can accelerate any milestone. See a chapter marked 🚧 Planned in a part's `README.md`? That's an open invitation — see [CONTRIBUTING.md](CONTRIBUTING.md).

## Non-Goals

- This is not a framework-agnostic textbook — code examples are opinionated (Python + FastAPI) by design, for consistency. Concepts transfer; syntax is illustrative.
- This is not a certification prep resource — it optimizes for real understanding over exam-style trivia (though the interview questions overlap significantly with what real interviews ask).

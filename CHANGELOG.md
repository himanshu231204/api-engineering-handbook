# Changelog

All notable changes to this project are documented here. Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- **Readability pass:** every written chapter now opens with a TL;DR callout ("In one line" / "In plain English" / "You'll be able to") and ends with a 3-question **Check Yourself** quiz with hidden answers.
- **Hand-drawn SVG concept diagrams** in `docs/assets/diagrams/` (HTTP anatomy, DNS, TLS, JWT, OAuth 2.0, circuit breaker, token bucket, cache-aside, queues, webhooks, tokenization, RAG pipeline, agent loop, MCP and more), embedded in their chapters and collected on the site's Diagrams page.
- **Redesigned GitHub Pages site:** full chapter navigation in the sidebar, generated from the part status tables; four learning tracks as top tabs; prev/next links; "Part N · Chapter k of M" crumbs; progress bars on part pages; fixed brand colours and dark-mode contrast; new home page with a learning-path diagram.
- `docs/study-plan.md` (three week-by-week tracks) and a browser-saved Progress Tracker page.
- `scripts/check_svgs.py` and a strict `mkdocs build` job in CI.
- `CLAUDE.md` and `AGENTS.md` — conventions for AI coding agents working in this repo (chapter template, status model, cross-linking rules, verification scripts).
- `.github/workflows/ci.yml` — link check + examples compile check on every push/PR, plus an advisory markdownlint pass.
- `scripts/check_links.py` and `scripts/check_examples_compile.py`.
- `.github/PULL_REQUEST_TEMPLATE.md` and `.github/ISSUE_TEMPLATE/` (bug report, chapter request).
- **50 chapters across Parts 5–13 and 18 are not yet written** (marked 🚧 Planned in their part READMEs). Parts 0–4, 14–17, and 19 are complete.
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
- Corrected README status tables for Parts 5–13 and 18: flipped 50 chapters from ✅ Written back to 🚧 Planned where the chapter files don't exist on disk; `scripts/check_links.py` reports 0 broken links in `docs/`.

## [0.1.0] — Initial scaffold
- Project initialized.

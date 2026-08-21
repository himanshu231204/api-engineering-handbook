# Changelog

All notable changes to this project are documented here. Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- `CLAUDE.md` and `AGENTS.md` — conventions for AI coding agents working in this repo (chapter template, status model, cross-linking rules, verification scripts).
- `.github/workflows/ci.yml` — link check + examples compile check on every push/PR, plus an advisory markdownlint pass.
- `scripts/check_links.py` and `scripts/check_examples_compile.py`.
- `.github/PULL_REQUEST_TEMPLATE.md` and `.github/ISSUE_TEMPLATE/` (bug report, chapter request).
- **All 190 chapters across all 20 parts are now written.** Every part's `README.md` status table is 100% ✅ Written — Parts 5–13 and 18 went from a curated subset to fully complete (Auth, Production Reliability, Caching, Async Systems, Realtime & Webhooks, API Security, Microservices, Observability, API Testing, Production Architecture).
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
- Repaired stray cross-part links (wrong filenames, links to not-yet-written chapters) discovered while completing Parts 5–13 and 18; `scripts/check_links.py` now reports 0 broken links across 269 Markdown files.

## [0.1.0] — Initial scaffold
- Project initialized.

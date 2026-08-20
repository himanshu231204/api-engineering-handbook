# CLAUDE.md

Guidance for Claude (and other coding agents) working in this repository. Read this before adding, editing, or restructuring content.

## What this repo is

`api-engineering-handbook` is an open-source, educational handbook: HTTP fundamentals → REST → FastAPI → databases → auth → production reliability → caching/async → realtime → security → microservices → observability → testing → LLM APIs → production AI systems → RAG → AI agents/MCP → production architecture → system design case studies → capstone projects. It is prose + diagrams + runnable code, not a framework or application — there is no build/test command for the repository as a whole. Individual `examples/*` directories are independently runnable Python projects; see each one's own `README.md`.

## Repository map

```
docs/<NN-slug>/          20 parts + 00-introduction. Each part has a README.md (index + status table) and chapter files.
examples/<name>/         Small, focused, runnable code samples. Each has its own README.md, requirements.txt.
projects/<NN-slug>/      10 capstone project specs (README.md each) — specs, not full implementations (a few may gain reference implementations over time).
diagrams/                6 standalone Mermaid diagram reference files.
resources/               cheatsheets/, interview-questions/, exercises/, glossary.md.
```

Part folder slugs (exact, used in every cross-link): `00-introduction, 01-api-foundations, 02-rest-api-design, 03-building-apis, 04-databases-and-apis, 05-authentication-authorization, 06-production-reliability, 07-caching-performance, 08-async-systems, 09-realtime-and-webhooks, 10-api-security, 11-microservices-distributed-systems, 12-observability, 13-api-testing, 14-ai-api-engineering, 15-production-ai-systems, 16-rag-apis, 17-ai-agents-and-mcp, 18-production-architecture, 19-system-design-case-studies, 20-capstone-projects`.

## Status model — read this before writing a chapter

Every part's `docs/<slug>/README.md` has a chapter table with a Status column:

- **✅ Written** — the chapter file exists and is linked: `| N | [Title](file.md) | ✅ Written |`
- **🚧 Planned** — the chapter is scoped but the file does **not** exist yet. It appears as **plain text, not a link**: `| N | Title | 🚧 Planned |`. Do not create a stub file for a Planned chapter and do not link to a file that doesn't exist — a link to a missing file is a broken link.

When you write a Planned chapter: create the file, then flip that row in the part's `README.md` from plain text + 🚧 Planned to a Markdown link + ✅ Written, matching the exact format above. Don't touch any other row.

Part 4 (Databases & APIs), Parts 1–3, and Parts 14–17 are fully written (every chapter). Parts 5–13 and 18 have a deliberately curated subset written, with the rest genuinely planned — check each README before assuming a chapter exists.

## The chapter template

Every chapter under `docs/` (except Part 19's case studies and `projects/*/README.md`, which have their own templates below) follows this exact section order. Skip a section only when it truly doesn't apply — that's rare.

```markdown
# Topic Name

## Why This Matters
## Core Concept
## Mental Model
## How It Works
## Architecture
## Request / Response Example
## Code Example
## Production Considerations
## Common Mistakes
## Best Practices
## AI Engineering Perspective
## Exercises
## Key Takeaways
```

Depth bar: ~1200–2200 words of real technical content (900+ is fine for the simplest Part 1 topics). Teach from first principles — problem → why it exists → basic solution → internal mechanics → real example → trade-offs → production implications. Never write a shallow one-liner definition. At least one Mermaid diagram in "Architecture." A real, correct, commented code example (Python + FastAPI + Pydantic v2 + SQLAlchemy async for backend chapters; illustrative pseudo-SDK calls with clear comments for LLM-provider-specific code, since we don't commit to one vendor SDK). Never hardcode secrets — always environment variables. "AI Engineering Perspective" should be a genuine connection, not a forced one; for chapters inside Parts 14–17 (already AI-native), use that section to go *deeper* — cross-references to RAG/agents/gateways — rather than restating that the topic is AI-related. Exercises: 1–2 each for Beginner / Intermediate / Advanced. Key Takeaways: 3–5 bullets.

### Part 19 (system design case studies) template

```markdown
# Design [a/an] <System>

## Problem Statement
## Requirements
### Functional Requirements
### Non-Functional Requirements
## Capacity Estimates
## API Design
## Database Design
## High-Level Architecture
## Data Flow
## Scaling Strategy
## Failure Handling
## Security
## Trade-offs
## Related Handbook Chapters
```

Capacity estimates need real back-of-envelope arithmetic with stated assumptions. Trade-offs must be genuine (a real alternative, seriously considered, with a real reason it was rejected) — not filler.

### `projects/NN-slug/README.md` template

```markdown
# Project N — <Title>

## Goal
## Builds On
## Requirements
## Architecture
## API Endpoints
## Database Schema
## Suggested Folder Structure
## Step-by-Step Implementation Plan
## Advanced Improvements
## Production Checklist
```

## Cross-linking rules

- Link to sibling chapters within the same part with a bare relative filename: `jwt-deeply-explained.md`.
- Link to another part's index with `../<slug>/README.md` — all 20 exist, always safe to link.
- **Only** link to a specific chapter file in another part if you have confirmed it exists (check the part's README status table, or `ls` the directory). If you're not sure, link to that part's `README.md` instead of guessing a filename.
- From `examples/*` or `projects/*`, the relative prefix to `docs/` is `../../docs/...`.
- Never link to a 🚧 Planned chapter's filename — mention it in prose without a link, or link to the part's `README.md`.
- After adding/removing/renaming any file, re-run the link check (see below) before committing.

## Verifying the repo

CI (`.github/workflows/ci.yml`) runs on every push/PR to `main` and does three things — run the same checks locally before committing:

```bash
python3 scripts/check_links.py              # every relative Markdown link must resolve — this is the hard gate
python3 scripts/check_examples_compile.py    # every examples/*.py must byte-compile — syntax gate, not a runtime test
```

Both scripts are stdlib-only (no install needed). Zero broken links is the bar — this repo has held at 0 through every content addition so far. A third CI job runs `markdownlint-cli2` against `.markdownlint.jsonc` in advisory mode (`continue-on-error: true`) — it won't block anything, but read its output.

For an `examples/*` project, "verify" means: `python3 scripts/check_examples_compile.py` at minimum, and actually running the example (installing its `requirements.txt` and following its own README) whenever you have the ability to.

## Working at scale (writing many chapters)

Chapters are large (1200–2200 words each with a diagram and code) and independent by file, which makes them a good fit for parallel subagents — one agent per part (or per priority subset within a part), each restricted to writing files only inside its own `docs/<slug>/` directory and updating only that part's own `README.md` status table. See recent git log messages (`docs: write Part N, ... chapters`) for the pattern this repo was actually built with. Don't have two agents write into the same directory concurrently.

## House rules

- No placeholder text (`TODO`, `coming soon`, lorem ipsum) in any committed chapter — either it's fully written or it's a 🚧 Planned row with no file.
- Don't rewrite the shared chapter template itself without updating this file, `CONTRIBUTING.md`, and every already-written chapter (i.e., don't).
- Prefer many focused commits (`docs: write Part N chapters`, `fix: repair broken links`) over one giant commit.
- Root files (`README.md`, `ROADMAP.md`, `CHANGELOG.md`) should be updated when a part's status changes — flip the milestone in `ROADMAP.md` and add a line to `CHANGELOG.md`'s `[Unreleased]` section.

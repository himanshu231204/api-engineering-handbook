# AGENTS.md

Instructions for AI coding agents (Claude, Codex, Cursor, Copilot Workspace, etc.) operating in this repository. Claude-specific tooling notes live in `CLAUDE.md`; the content rules below apply to every agent regardless of tool.

## Project type

`api-engineering-handbook` is a documentation-and-examples repository, not an application. There is no single build, no server to start for the repo as a whole, and no top-level test suite. It has two kinds of content:

1. **Markdown chapters** (`docs/`, `projects/`, `diagrams/`, `resources/`) — the handbook itself.
2. **Runnable Python examples** (`examples/*/`) — small, independent projects, each with its own `README.md` and `requirements.txt`.

Treat these differently: Markdown changes need a link check (below); example changes need the code to actually run.

## Repository layout

```
README.md, LICENSE, CONTRIBUTING.md, CODE_OF_CONDUCT.md, ROADMAP.md, CHANGELOG.md
docs/00-introduction/ … docs/20-capstone-projects/   20 parts, each: README.md (index + status table) + chapter files
examples/<name>/                                     runnable code samples, own README + requirements.txt
projects/<NN-slug>/                                  10 capstone project specs (README.md)
diagrams/                                             6 standalone Mermaid diagram files
resources/cheatsheets/, interview-questions/, exercises/, glossary.md
```

Exact part slugs (use these, not paraphrases, in every path and link): `00-introduction`, `01-api-foundations`, `02-rest-api-design`, `03-building-apis`, `04-databases-and-apis`, `05-authentication-authorization`, `06-production-reliability`, `07-caching-performance`, `08-async-systems`, `09-realtime-and-webhooks`, `10-api-security`, `11-microservices-distributed-systems`, `12-observability`, `13-api-testing`, `14-ai-api-engineering`, `15-production-ai-systems`, `16-rag-apis`, `17-ai-agents-and-mcp`, `18-production-architecture`, `19-system-design-case-studies`, `20-capstone-projects`.

## Setup / build / test commands

- **Markdown content**: no install needed. Just edit and run `python3 scripts/check_links.py` (see "Verification" below) before committing.
- **An `examples/*` project**: `cd examples/<name>`, create a venv, `pip install -r requirements.txt`, then follow that example's own `README.md` for run instructions. Copy `.env.example` to `.env` and fill in real values where one exists — never commit a real `.env`.
- Repository-wide CI lives in `.github/workflows/ci.yml` and runs on every push/PR to `main`: `scripts/check_links.py`, `scripts/check_examples_compile.py`, and an advisory `markdownlint-cli2` pass (`.markdownlint.jsonc`, non-blocking).

## Status model (chapters)

Each part's `docs/<slug>/README.md` has a chapter table. A row is either:

- `| N | [Title](file.md) | ✅ Written |` — the file exists.
- `| N | Title | 🚧 Planned |` — scoped, but no file yet, and deliberately **not** a link.

Never create a stub for a 🚧 Planned row and never link to a chapter file that doesn't exist yet. When you write a Planned chapter, flip its row to the ✅ Written / linked form shown above — nothing else in that README should change. Parts 1–4 and 14–17 are complete (every chapter written); Parts 5–13 and 18 are a curated subset with real gaps remaining — check the table, don't assume.

## Chapter template (docs/, except Part 19 and projects/)

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

Rules: ~1200–2200 words, first-principles teaching (problem → why → solution → mechanics → example → trade-offs → production reality), at least one Mermaid diagram under "Architecture," real runnable-looking code (Python/FastAPI/Pydantic v2/SQLAlchemy async), no hardcoded secrets, "AI Engineering Perspective" only where the connection is genuine, tiered exercises (Beginner/Intermediate/Advanced), 3–5 key takeaways. No placeholder text ever in a committed file.

**Part 19 case studies** use a different template: Problem Statement → Requirements (Functional/Non-Functional) → Capacity Estimates (real arithmetic, stated assumptions) → API Design → Database Design → High-Level Architecture (Mermaid) → Data Flow → Scaling Strategy → Failure Handling → Security → Trade-offs (genuine, not filler) → Related Handbook Chapters.

**`projects/NN-slug/README.md`** uses: Goal → Builds On → Requirements → Architecture (Mermaid) → API Endpoints → Database Schema → Suggested Folder Structure → Step-by-Step Implementation Plan → Advanced Improvements → Production Checklist.

## Learner aids (every chapter, including Part 19 case studies)

Two additions sit *around* the template — they don't add or reorder `##` sections:

1. **TL;DR callout**, directly under the `# Title` line:

   ```markdown
   > [!TIP]
   > **In one line:** <the single most important idea, ≤ 30 words>
   >
   > **In plain English:** <2–3 jargon-free sentences>
   >
   > **You'll be able to:** <outcome> · <outcome> · <outcome>
   ```

   GitHub renders `> [!TIP]` natively; `scripts/mkdocs_hooks.py` converts it to a styled "TL;DR" box on the Pages site.
2. **Check Yourself quiz** — a `### Check Yourself` H3 at the end of `## Key Takeaways` (end of file for Part 19) with 3 questions (recall, why/what-if, applied scenario), each as `<details markdown="1"><summary>N. Question</summary>` + blank line + answer + blank line + `</details>`. Blank lines and `markdown="1"` are required.

## SVG concept diagrams

Hand-drawn SVGs live in `docs/assets/diagrams/<NN>-<name>.svg` (NN = part number) and are embedded with `![alt text](../assets/diagrams/<NN>-<name>.svg)`. Copy the visual system of `docs/assets/diagrams/01-http-request-anatomy.svg`: width 880, own white rounded background (so it reads in dark mode), `<title>`/`<desc>`, the same `<style>` classes, the fixed palette (green = main path, blue = client/info, amber = data, red = failure, purple = AI/external, slate = infra), numbered circles for ordered steps, no text under 12px. Escape `&` as `&amp;`. They supplement Mermaid diagrams, they don't replace them. The site's Diagrams page lists every SVG automatically.

## Cross-linking rules

- Sibling chapter in the same part: bare relative filename (`oauth2.md`).
- Another part's index: `../<slug>/README.md` (always safe — all 20 exist).
- A specific chapter in another part: only if you've confirmed it exists (check that part's status table or list its directory). If unsure, link the part's `README.md` instead.
- From `examples/*` or `projects/*` to `docs/`: prefix is `../../docs/...`.
- Never link a 🚧 Planned chapter's filename.

## Verification before committing

Run both from the repo root and fix anything they report — the repo has held at 0 broken links through every prior change:

```bash
python3 scripts/check_links.py
python3 scripts/check_examples_compile.py
```

Both are stdlib-only, no install required. These are exactly the checks `.github/workflows/ci.yml` runs on every push/PR to `main`.

For an `examples/*` change: `scripts/check_examples_compile.py` is the syntax floor; actually run the example end-to-end if you have the ability to install its `requirements.txt`.

## Commit and PR conventions

- Conventional-ish prefixes: `docs: write Part N chapters`, `fix: repair broken links`, `feat: add example X`, `chore: ...`.
- One logical unit of work per commit; don't mix a content addition with an unrelated structural change.
- When a part's completion status changes, update `ROADMAP.md`'s milestone checklist and add a line under `[Unreleased]` in `CHANGELOG.md`.
- Follow `CONTRIBUTING.md`'s PR checklist (template compliance, working links, status table updated, no secrets in the diff).

## Parallelizing large content work

Chapters are self-contained by file, so writing many at once splits cleanly by part: give each worker exactly one part directory to write into and its own part's `README.md` to update, tell it the precise list of filenames and titles, and don't let two workers touch the same directory concurrently. This is how the bulk of the handbook was actually produced — see the `docs: write Part N, ...` commits in git log for the pattern.

## Things not to do

- Don't invent a chapter filename that isn't in the part's status table.
- Don't hardcode API keys, DB credentials, or webhook secrets anywhere, including in example `.env` files (use `.env.example` with placeholder values).
- Don't change the shared templates above without updating `CLAUDE.md`, `CONTRIBUTING.md`, and this file together.
- Don't commit an empty/stub chapter file — either it's real and complete, or it stays a 🚧 Planned row with no file.

# Contributing to the API Engineering Handbook

Thanks for considering a contribution. This handbook is meant to be a living, community-improvable resource, and contributions of all sizes are welcome — from fixing a typo to writing a whole planned chapter.

## Ways to Contribute

- **Fix errors** — technical inaccuracies, broken links, outdated APIs, typos.
- **Improve explanations** — if a section confused you, it will confuse others; open an issue or send a PR that clarifies it.
- **Add diagrams** — Mermaid diagrams or hand-drawn SVGs (see "Learner aids & SVG diagrams" below) are always welcome, especially for text-heavy chapters.
- **Write a planned chapter** — check a Part's `README.md` for chapters marked 🚧 Planned.
- **Add exercises or interview questions** — see `resources/exercises/` and `resources/interview-questions/`.
- **Improve or add code examples** — see `examples/`.
- **Translate** — translations are welcome as a top-level `i18n/<lang>/` mirror of `docs/` (open an issue first to coordinate).

## Before You Start

1. **Check open issues and PRs** to avoid duplicate work.
2. **For a new chapter or a large restructuring**, open an issue first describing what you plan to write, so it can be discussed before you invest the time.
3. **Small fixes** (typos, broken links, small clarifications) can go straight to a PR.

## Chapter Format

Every chapter should follow the shared template used throughout `docs/`:

```markdown
# Topic Name

## Why This Matters
## Core Concept
## Mental Model
## How It Works
## Architecture           (Mermaid diagram where useful)
## Request / Response Example
## Code Example           (Python + FastAPI preferred for backend chapters)
## Production Considerations
## Common Mistakes
## Best Practices
## AI Engineering Perspective   (where relevant)
## Exercises
## Key Takeaways
```

### Learner aids & SVG diagrams

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

**SVG concept diagrams.**

Hand-drawn SVGs live in `docs/assets/diagrams/<NN>-<name>.svg` (NN = part number) and are embedded with `![alt text](../assets/diagrams/<NN>-<name>.svg)`. Copy the visual system of `docs/assets/diagrams/01-http-request-anatomy.svg`: width 880, own white rounded background (so it reads in dark mode), `<title>`/`<desc>`, the same `<style>` classes, the fixed palette (green = main path, blue = client/info, amber = data, red = failure, purple = AI/external, slate = infra), numbered circles for ordered steps, no text under 12px. Escape `&` as `&amp;`. They supplement Mermaid diagrams, they don't replace them. The site's Diagrams page lists every SVG automatically.

Not every section applies to every topic (a chapter on JSON serialization doesn't need an "AI Engineering Perspective" section, for example) — use judgment, but keep the overall shape consistent so readers know what to expect.

Writing style:

- Beginner-friendly but technically accurate — explain the problem before the solution.
- Prefer concrete examples over abstract descriptions.
- Code examples must run, use environment variables for secrets (never hardcode credentials), and include comments where the "why" isn't obvious.
- Keep Mermaid diagrams simple — a diagram that needs its own explanation has failed at being a diagram.

## Pull Request Checklist

- [ ] Chapter follows the shared template (where applicable).
- [ ] Chapter has the TL;DR callout and a 3-question Check Yourself quiz, and `python3 scripts/check_chapters.py` passes.
- [ ] New SVGs pass `python3 scripts/check_svgs.py`, and `mkdocs build --strict` passes (`pip install -r requirements-docs.txt`).
- [ ] Internal links use relative paths and resolve correctly — run `python3 scripts/check_links.py` locally (this also runs in CI on every push/PR).
- [ ] New chapters are linked from their Part's `README.md` and its status is updated from 🚧 Planned to ✅ Written.
- [ ] Code examples were actually run. If you touched anything under `examples/`, `python3 scripts/check_examples_compile.py` should also pass (CI checks this too, but it's a syntax check only — actually running the example is still on you).
- [ ] No hardcoded secrets, API keys, or credentials anywhere in the diff.
- [ ] Spelling/grammar checked.

## Continuous Integration

Every push and pull request to `main` runs `.github/workflows/ci.yml`, which:

1. Runs `scripts/check_links.py` — fails the build if any relative Markdown link is broken.
2. Runs `scripts/check_examples_compile.py` — byte-compiles every `.py` file under `examples/` as a fast syntax gate (it does not install dependencies or execute the examples).
3. Runs `markdownlint-cli2` in advisory mode (`continue-on-error: true`) against a relaxed ruleset in `.markdownlint.jsonc` — it won't block a PR, but its output is worth reading.

Both scripts under `scripts/` are safe to run locally with no dependencies beyond the Python standard library.

## Reporting Issues

Use the issue templates under `.github/ISSUE_TEMPLATE/`:

- **Bug report / content error** — factual error, broken link, outdated code, typo, or inconsistency. Include the file/chapter affected, what's wrong, and a suggested fix if you have one.
- **New / planned chapter** — propose writing a chapter that's marked 🚧 Planned in a Part's `README.md`, or one you think is missing entirely.

## Opening a Pull Request

PRs use the template at `.github/PULL_REQUEST_TEMPLATE.md`, which mirrors the checklist above (chapter template compliance, status table updated, links verified, no secrets). Fill in what applies and delete the rest for small fixes.

## Code of Conduct

By participating in this project you agree to abide by the [Code of Conduct](CODE_OF_CONDUCT.md).

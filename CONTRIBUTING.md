# Contributing to the API Engineering Handbook

Thanks for considering a contribution. This handbook is meant to be a living, community-improvable resource, and contributions of all sizes are welcome — from fixing a typo to writing a whole planned chapter.

## Ways to Contribute

- **Fix errors** — technical inaccuracies, broken links, outdated APIs, typos.
- **Improve explanations** — if a section confused you, it will confuse others; open an issue or send a PR that clarifies it.
- **Add diagrams** — more Mermaid diagrams are almost always welcome, especially for chapters that are text-heavy.
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

Not every section applies to every topic (a chapter on JSON serialization doesn't need an "AI Engineering Perspective" section, for example) — use judgment, but keep the overall shape consistent so readers know what to expect.

Writing style:

- Beginner-friendly but technically accurate — explain the problem before the solution.
- Prefer concrete examples over abstract descriptions.
- Code examples must run, use environment variables for secrets (never hardcode credentials), and include comments where the "why" isn't obvious.
- Keep Mermaid diagrams simple — a diagram that needs its own explanation has failed at being a diagram.

## Pull Request Checklist

- [ ] Chapter follows the shared template (where applicable).
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

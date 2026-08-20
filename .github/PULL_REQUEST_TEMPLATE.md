<!--
Thanks for contributing to the API Engineering Handbook! Please read CONTRIBUTING.md
before opening a large PR (new chapter, restructuring). Fill in what's relevant and
delete the rest — small fixes (typos, broken links) don't need every section filled.
-->

## What does this PR do?

<!-- One or two sentences. Is this a new chapter, a fix, an example, a resource, or something else? -->

## Type of change

- [ ] New chapter (docs/, projects/, or docs/19-system-design-case-studies/)
- [ ] Fix (typo, factual error, broken link, outdated code)
- [ ] New or updated runnable example (examples/)
- [ ] New or updated resource (cheatsheet, glossary entry, interview question, exercise)
- [ ] Diagram (diagrams/)
- [ ] Repo/tooling change (CI, templates, root docs)
- [ ] Other (describe above)

## If this adds or completes a chapter

- [ ] Follows the shared chapter template exactly (see `CONTRIBUTING.md` / `CLAUDE.md` for the section list).
- [ ] Includes at least one Mermaid diagram under "Architecture."
- [ ] Includes a real, correct, commented code example — no hardcoded secrets anywhere.
- [ ] The relevant Part's `README.md` chapter table is updated: the row now links to the file and its status changed from 🚧 Planned to ✅ Written.
- [ ] Word count is roughly in the expected range for this chapter's part (see `CLAUDE.md`) — not a shallow stub.

## If this touches `examples/`

- [ ] The example has its own `README.md` explaining what it demonstrates, how to run it, and which handbook chapter it accompanies.
- [ ] `requirements.txt` is present and accurate.
- [ ] No real secrets committed — only `.env.example` with placeholder values, never a real `.env`.
- [ ] You actually ran the example, or at minimum it passes `python3 scripts/check_examples_compile.py`.

## Verification

- [ ] `python3 scripts/check_links.py` passes locally (this also runs in CI).
- [ ] `python3 scripts/check_examples_compile.py` passes locally, if `examples/` was touched.
- [ ] Spelling/grammar checked.
- [ ] No unrelated changes bundled into this PR.

## Related issue

<!-- Closes #123, or "N/A" -->

## Anything else reviewers should know?

<!-- Open questions, things you're unsure about, alternatives you considered -->

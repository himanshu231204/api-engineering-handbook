#!/usr/bin/env python3
"""Check every chapter under docs/ follows the handbook's template and learner aids.

Hard failures (exit 1): the required H2 sections out of order or missing, no TL;DR
callout directly under the H1, not exactly one '### Check Yourself' with three quiz
<details> blocks, unbalanced code fences, placeholder text, stray tool markup.
Warnings only: chapters shorter than ~900 words of prose.

Scope: every docs/NN-slug/*.md except README.md files and Part 0 (an orientation part
with its own shape). Part 19 case studies use their own section list, so only the
TL;DR and quiz are checked there. See CLAUDE.md for the template.

Stdlib only; used by CI. Usage: python3 scripts/check_chapters.py
"""

import re
import sys
from pathlib import Path

DOCS = Path("docs")
TEMPLATE = [
    "Why This Matters", "Core Concept", "Mental Model", "How It Works", "Architecture",
    "Request / Response Example", "Code Example", "Production Considerations",
    "Common Mistakes", "Best Practices", "AI Engineering Perspective", "Exercises",
    "Key Takeaways",
]
PLACEHOLDER = re.compile(r"\b(TODO|TBD|FIXME|lorem ipsum|coming soon)\b", re.I)
TLDR = re.compile(r"# [^\n]+\n\n> \[!TIP\]\n> \*\*In one line:\*\* [^\n]+\n>\n> \*\*In plain English:\*\* ")
MIN_WORDS = 900


def check(path: Path) -> tuple[list[str], list[str]]:
    s = path.read_text(encoding="utf-8")
    errors, warnings = [], []
    part19 = path.parent.name.startswith("19-")

    if not TLDR.match(s) or "**You'll be able to:**" not in s:
        errors.append("missing or malformed TL;DR callout right after the H1")
    if s.count("### Check Yourself") != 1:
        errors.append("needs exactly one '### Check Yourself'")
    if s.count('<details markdown="1">') != 3 or s.count("</details>") != 3:
        errors.append('quiz needs exactly 3 <details markdown="1"> blocks')
    if s.count("```") % 2:
        errors.append("unbalanced code fences")
    if PLACEHOLDER.search(s):
        errors.append("placeholder text (TODO/TBD/coming soon/lorem ipsum)")
    if "</content>" in s or "<parameter" in s:
        errors.append("stray tool markup")

    if not part19:
        h2 = [re.sub(r"\s*\(.*\)$", "", h) for h in re.findall(r"^## (.+)$", s, re.M)]
        if h2 != TEMPLATE:
            errors.append(f"H2 sections must follow the chapter template in order; got {h2}")
        elif s.find("### Check Yourself") < s.find("## Key Takeaways"):
            errors.append("Check Yourself must come inside Key Takeaways")
        if "```mermaid" not in s:
            errors.append("no Mermaid diagram")

    prose = re.sub(r"```.*?```", "", s, flags=re.S)
    words = len(re.findall(r"\w+", prose))
    if words < MIN_WORDS:
        warnings.append(f"short chapter ({words} words of prose)")
    return errors, warnings


def main() -> int:
    files = sorted(
        p for p in DOCS.glob("[0-9][0-9]-*/*.md")
        if p.name != "README.md" and not p.parent.name.startswith("00-")
    )
    failed = 0
    for path in files:
        errors, warnings = check(path)
        for w in warnings:
            print(f"warning: {path}: {w}")
        if errors:
            failed += 1
            print(f"FAIL {path}")
            for e in errors:
                print(f"   - {e}")
    print(f"Checked {len(files)} chapters.")
    if failed:
        print(f"{failed} chapter(s) failed.")
        return 1
    print("All chapters follow the template and learner-aid conventions. ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())

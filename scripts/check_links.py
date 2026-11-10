#!/usr/bin/env python3
"""Check every relative Markdown link in the repository resolves to a real file.

Used by CI (.github/workflows/ci.yml) and by CONTRIBUTING.md / CLAUDE.md / AGENTS.md
as the verification step before committing a content change.

Usage:
    python3 scripts/check_links.py

Exits 0 with a summary if every relative link resolves, exits 1 and prints each
broken link ("file", "raw target") otherwise. External links (http/https/mailto)
and pure in-page anchors (#section) are skipped — this only checks that files
referenced by relative path actually exist.
"""

import os
import re
import sys

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
CODE_FENCE_RE = re.compile(r"```.*?```", re.S)
INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}


def find_markdown_files(root: str) -> list[str]:
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.endswith(".md"):
                files.append(os.path.join(dirpath, name))
    return files


def check(root: str) -> list[tuple[str, str]]:
    broken = []
    for md_path in find_markdown_files(root):
        with open(md_path, encoding="utf-8") as fh:
            content = fh.read()
        # Strip fenced code blocks and inline code spans so code like `f(**kwargs)` or an
        # illustrative `[Title](file.md)` snippet never false-positives as a real link.
        content_no_code = CODE_FENCE_RE.sub("", content)
        content_no_code = INLINE_CODE_RE.sub("", content_no_code)
        for match in LINK_RE.finditer(content_no_code):
            target = match.group(1).strip()
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path_part = target.split("#", 1)[0]
            if not path_part:
                continue
            resolved = os.path.normpath(os.path.join(os.path.dirname(md_path), path_part))
            if not os.path.exists(resolved):
                broken.append((os.path.relpath(md_path, root), target))
    return broken


def main() -> int:
    root = os.getcwd()
    md_files = find_markdown_files(root)
    broken = check(root)

    print(f"Checked {len(md_files)} Markdown files.")
    if broken:
        print(f"\n{len(broken)} broken link(s):\n")
        for file_path, target in broken:
            print(f"  {file_path} -> {target}")
        return 1

    print("All relative links resolve. ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())

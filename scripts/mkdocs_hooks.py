"""mkdocs build hook: fix cross-directory links for the built site.

Chapters, projects, and resources are authored with relative links that
assume the *repository* layout (e.g. "../../resources/glossary.md" from a
docs/<part>/ chapter). In the MkDocs site, docs/ is the site root, so those
links need re-basing — and links into examples/ or the root README, which
aren't part of the docs site at all, need to become absolute GitHub URLs.

Runs on every page at build time; the source Markdown files are untouched.
"""

import re

GITHUB_BASE = "https://github.com/himanshu231204/api-engineering-handbook"

_LINK = re.compile(r"\((?:\.\./)+(resources|projects|diagrams|examples|README\.md)(/[^)]*)?\)")


def on_page_markdown(markdown, page, config, files):
    depth = page.file.src_uri.count("/")

    def repl(match):
        target, rest = match.group(1), match.group(2) or ""
        if target in ("resources", "projects", "diagrams"):
            if rest.endswith("/") or rest == "":
                # A bare subdirectory link (e.g. "projects/01-crud-api/") — that
                # project/part has its own README.md, so point straight at it.
                # Anything else without one falls back to the section index.
                rest = f"{rest.rstrip('/')}/README.md" if target == "projects" and rest not in ("", "/") else "/index.md"
            return f"({'../' * depth}{target}{rest})"
        if target == "examples":
            return f"({GITHUB_BASE}/tree/main/examples{rest})"
        return f"({GITHUB_BASE}/blob/main/README.md)"

    return _LINK.sub(repl, markdown)

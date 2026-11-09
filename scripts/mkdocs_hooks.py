"""mkdocs build hook: fix cross-directory links for the built site.

Chapters, projects, and resources are authored with relative links that
assume the *repository* layout (e.g. "../../resources/glossary.md" from a
docs/<part>/ chapter). In the MkDocs site, docs/ is the site root, so those
links need re-basing — and links into examples/ or the root README, which
aren't part of the docs site at all, need to become absolute GitHub URLs.

Runs on every page at build time; the source Markdown files are untouched.
"""

import os
import re

GITHUB_BASE = "https://github.com/himanshu231204/api-engineering-handbook"

_LINK = re.compile(r"\((?:\.\./)+(resources|projects|diagrams|examples|README\.md)(/[^)]*)?\)")


# GitHub-style alerts ("> [!TIP]" blockquotes) render natively on github.com.
# Convert them to Material admonitions so they render as styled callouts on the
# Pages site too. Authors write one syntax; both surfaces look right.
_ALERT_TYPES = {
    "NOTE": ("note", "Note"),
    "TIP": ("tip", "TL;DR"),
    "IMPORTANT": ("abstract", "Important"),
    "WARNING": ("warning", "Warning"),
    "CAUTION": ("danger", "Caution"),
}
_ALERT_START = re.compile(r"^> ?\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\][ \t]*(.*)$")


def _convert_alerts(markdown: str) -> str:
    out: list[str] = []
    lines = markdown.split("\n")
    i = 0
    in_fence = False
    while i < len(lines):
        line = lines[i]
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
        match = None if in_fence else _ALERT_START.match(line)
        if not match:
            out.append(line)
            i += 1
            continue
        kind, title = _ALERT_TYPES[match.group(1)]
        title = match.group(2).strip() or title
        body: list[str] = []
        i += 1
        while i < len(lines) and lines[i].startswith(">"):
            body.append(lines[i][2:] if lines[i].startswith("> ") else lines[i][1:])
            i += 1
        out.append(f'!!! {kind} "{title}"')
        out.append("")
        out.extend(f"    {b}" if b.strip() else "" for b in body)
        out.append("")
    return "\n".join(out)


# ---- part progress bars + chapter "where am I" crumbs -------------------------
_PART_DIR = re.compile(r"^(\d\d)-[a-z0-9-]+$")
_ROW = re.compile(r"^\|\s*\d+\s*\|(.*)\|\s*(✅|🚧)[^|]*\|\s*$")
_ROW_FILE = re.compile(r"\]\(([^)/]+\.md)\)")
_PARTS: dict[str, dict] = {}


def on_config(config):
    """Read every part's README status table once per build."""
    _PARTS.clear()
    docs_dir = config["docs_dir"]
    for name in sorted(os.listdir(docs_dir)):
        readme = os.path.join(docs_dir, name, "README.md")
        if not (_PART_DIR.match(name) and os.path.exists(readme)):
            continue
        with open(readme, encoding="utf-8") as fh:
            text = fh.read()
        title = next((l[2:].strip() for l in text.splitlines() if l.startswith("# ")), name)
        rows = [m for m in (_ROW.match(l) for l in text.splitlines()) if m]
        written = [f.group(1) for m in rows if m.group(2) == "✅" for f in [_ROW_FILE.search(m.group(1))] if f]
        _PARTS[name] = {
            "number": int(name[:2]),
            "title": re.sub(r"^Part \d+\s*[—-]\s*", "", title),
            "written": written,
            "done": sum(1 for m in rows if m.group(2) == "✅"),
            "total": len(rows),
        }
    return config


def _insert_after_h1(markdown: str, html: str) -> str:
    lines = markdown.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("# "):
            lines[i + 1 : i + 1] = ["", html, ""]
            return "\n".join(lines)
    return markdown


def _decorate(markdown: str, src_uri: str) -> str:
    folder, _, filename = src_uri.partition("/")
    part = _PARTS.get(folder)
    if not part or "/" in filename:
        return markdown
    if filename == "README.md":
        if not part["total"] or part["done"] == part["total"]:
            label = f"All {part['total']} chapters written" if part["total"] else ""
            pct = 100
        else:
            label = f"{part['done']} of {part['total']} chapters written · 🚧 rows are planned"
            pct = round(100 * part["done"] / part["total"])
        if not label:
            return markdown
        return _insert_after_h1(
            markdown,
            f'<div class="hb-progress"><div class="hb-progress-bar"><span style="width:{pct}%"></span></div>'
            f"<p>{label}</p></div>",
        )
    if filename in part["written"]:
        idx = part["written"].index(filename) + 1
        return _insert_after_h1(
            markdown,
            f'<p class="hb-crumb"><a href="../">Part {part["number"]} · {part["title"]}</a>'
            f"<span>·</span><span>Chapter {idx} of {len(part['written'])}</span></p>",
        )
    return markdown


def on_page_markdown(markdown, page, config, files):
    markdown = _convert_alerts(markdown)
    markdown = _decorate(markdown, page.file.src_uri)
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

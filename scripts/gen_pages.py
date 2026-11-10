"""mkdocs-gen-files hook: build the generated parts of the site.

Runs at build time (the source tree is never modified). It:

1. Mirrors projects/, resources/ and diagrams/ — which live outside docs_dir —
   into the build as virtual pages, with an index page for each section.
2. Writes SUMMARY.md, the site navigation read by mkdocs-literate-nav. Every
   part's chapters are taken from that part's README.md status table (only
   ✅ rows that link to a real file), so the sidebar, prev/next buttons and the
   README tables can never drift apart.
3. Writes a visual diagram gallery (every SVG in docs/assets/diagrams/,
   grouped by part, each linked to the chapter that uses it).
4. Writes progress.md — a per-chapter checklist learners can tick off
   (ticks are remembered in their browser by docs/javascripts/progress.js).
"""

import re
from pathlib import Path

import mkdocs_gen_files

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS = REPO_ROOT / "docs"

# projects/ and resources/ link to docs/ with paths like "../../docs/01-.../x.md".
# docs/ *is* the site root once mirrored in, so drop the "docs/" segment.
_DOCS_LINK = re.compile(r"(\((?:\.\./)+)docs/")
_ROW_LINK = re.compile(r"^\|\s*[^|]*\|\s*\[([^\]]+)\]\(([^)/]+\.md)\)\s*\|.*✅")
_PART_DIR = re.compile(r"^(\d\d)-")

# Top-level tabs: (tab title, first part, last part).
TRACKS = [
    ("Foundations", 0, 4),
    ("Backend in Production", 5, 13),
    ("AI Engineering", 14, 17),
    ("Architecture & Design", 18, 20),
]


def first_heading(text: str, fallback: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def mirror(source_dir: str, dest_prefix: str) -> list[tuple[str, str]]:
    """Copy every .md file under source_dir into dest_prefix/, return (title, dest_path) pairs."""
    entries = []
    src = REPO_ROOT / source_dir
    for md_file in sorted(src.rglob("*.md")):
        rel = md_file.relative_to(src)
        dest = f"{dest_prefix}/{rel.as_posix()}"
        content = _DOCS_LINK.sub(r"\1", md_file.read_text(encoding="utf-8"))
        with mkdocs_gen_files.open(dest, "w") as f:
            f.write(content)
        mkdocs_gen_files.set_edit_path(dest, Path(source_dir) / rel)
        entries.append((first_heading(content, rel.stem), dest))
    return entries


def parts() -> list[tuple[int, str, str, list[tuple[str, str]]]]:
    """Return (number, slug, part title, [(chapter title, path)]) for every part, in order."""
    result = []
    for part_dir in sorted(p for p in DOCS.iterdir() if p.is_dir() and _PART_DIR.match(p.name)):
        readme = part_dir / "README.md"
        if not readme.exists():
            continue
        text = readme.read_text(encoding="utf-8")
        title = first_heading(text, part_dir.name)
        chapters = []
        for line in text.splitlines():
            m = _ROW_LINK.match(line)
            if m and (part_dir / m.group(2)).exists():
                chapters.append((m.group(1).strip(), f"{part_dir.name}/{m.group(2)}"))
        result.append((int(part_dir.name[:2]), part_dir.name, title, chapters))
    return result


def short_part_title(number: int, title: str) -> str:
    # "Part 5 — Authentication & Authorization" -> "05 · Authentication & Authorization"
    name = re.sub(r"^Part \d+\s*[—-]\s*", "", title)
    return f"{number:02d} · {name}"


# ---------------------------------------------------------------- mirrors
project_entries = mirror("projects", "projects")
resource_entries = mirror("resources", "resources")
diagram_entries = mirror("diagrams", "diagrams")
PARTS = parts()

with mkdocs_gen_files.open("projects/index.md", "w") as f:
    f.write("# Capstone Projects\n\n")
    f.write(
        "Ten full project specs — goal, requirements, architecture, API "
        "design, database schema, and a production checklist for each.\n\n"
    )
    for title, dest in project_entries:
        f.write(f"- [{title}]({dest.removeprefix('projects/')})\n")

with mkdocs_gen_files.open("resources/index.md", "w") as f:
    f.write("# Resources\n\n")
    f.write("Cheatsheets, exercises, interview questions, and a glossary.\n\n")
    for title, dest in resource_entries:
        f.write(f"- [{title}]({dest.removeprefix('resources/')})\n")

# ---------------------------------------------------------------- diagram gallery
svgs = sorted((DOCS / "assets" / "diagrams").glob("*.svg"))
chapter_files = sorted(DOCS.glob("[0-9][0-9]-*/*.md"))


def svg_title(path: Path) -> str:
    m = re.search(r"<title[^>]*>(.*?)</title>", path.read_text(encoding="utf-8"), re.S)
    return m.group(1).strip() if m else path.stem


def used_in(svg_name: str) -> tuple[str, str] | None:
    for chapter in chapter_files:
        text = chapter.read_text(encoding="utf-8")
        if svg_name in text:
            return first_heading(text, chapter.stem), chapter.relative_to(DOCS).as_posix()
    return None


part_names = {n: short_part_title(n, t) for n, _, t, _ in PARTS}
with mkdocs_gen_files.open("diagrams/index.md", "w") as f:
    f.write("# Diagrams\n\n")
    f.write(
        "Every concept diagram in the handbook in one place — a fast way to revise. "
        "Click a diagram's chapter link to read the full explanation.\n\n"
    )
    current = None
    for svg in svgs:
        number = int(svg.name[:2]) if svg.name[:2].isdigit() else -1
        if number != current:
            current = number
            f.write(f"\n## {part_names.get(number, 'Other')}\n\n")
        title = svg_title(svg)
        f.write(f"### {title}\n\n")
        f.write(f'![{title}](../assets/diagrams/{svg.name}){{ loading=lazy }}\n\n')
        usage = used_in(svg.name)
        if usage:
            f.write(f"Explained in: [{usage[0]}](../{usage[1]})\n\n")
    f.write("\n## Mermaid reference diagrams\n\n")
    f.write("Larger end-to-end flows, drawn as Mermaid diagrams.\n\n")
    for title, dest in diagram_entries:
        f.write(f"- [{title}]({dest.removeprefix('diagrams/')})\n")

# ---------------------------------------------------------------- progress tracker
total = sum(len(ch) for number, _, _, ch in PARTS if number != 20)
with mkdocs_gen_files.open("progress.md", "w") as f:
    f.write("# Progress Tracker\n\n")
    f.write(
        f"Tick each chapter once you can answer its **Check Yourself** questions "
        f"without peeking. Your ticks are saved in this browser only.\n\n"
        f'<div class="hb-progress" data-total="{total}"><div class="hb-progress-bar">'
        f'<span></span></div><p><b class="hb-progress-done">0</b> of {total} chapters done</p></div>\n\n'
    )
    for number, slug, title, chapters in PARTS:
        if not chapters or number == 20:
            continue
        f.write(f"## [{short_part_title(number, title)}]({slug}/README.md)\n\n")
        for ch_title, path in chapters:
            f.write(f"- [ ] [{ch_title}]({path})\n")
        f.write("\n")

# ---------------------------------------------------------------- navigation
with mkdocs_gen_files.open("SUMMARY.md", "w") as nav:
    nav.write("- Start Here\n")
    nav.write("    - [Home](index.md)\n")
    nav.write("    - [Study Plan](study-plan.md)\n")
    nav.write("    - [Progress Tracker](progress.md)\n")
    for track, lo, hi in TRACKS:
        nav.write(f"- {track}\n")
        for number, slug, title, chapters in PARTS:
            if not lo <= number <= hi:
                continue
            nav.write(f"    - {short_part_title(number, title)}\n")
            nav.write(f"        - [Overview]({slug}/README.md)\n")
            for ch_title, path in chapters:
                nav.write(f"        - [{ch_title}]({path})\n")
    nav.write("- Projects\n")
    nav.write("    - [All Projects](projects/index.md)\n")
    for title, dest in project_entries:
        nav.write(f"    - [{title}]({dest})\n")
    nav.write("- Resources\n")
    nav.write("    - [All Resources](resources/index.md)\n")
    groups: dict[str, list[tuple[str, str]]] = {}
    for title, dest in resource_entries:
        parts_ = dest.split("/")
        group = parts_[1] if len(parts_) > 2 else ""
        groups.setdefault(group, []).append((title, dest))
    for title, dest in groups.pop("", []):
        nav.write(f"    - [{title}]({dest})\n")
    for group, items in groups.items():
        nav.write(f"    - {group.replace('-', ' ').title()}\n")
        for title, dest in items:
            nav.write(f"        - [{title}]({dest})\n")
    nav.write("- Diagrams\n")
    nav.write("    - [All Diagrams](diagrams/index.md)\n")
    for title, dest in diagram_entries:
        nav.write(f"    - [{title}]({dest})\n")

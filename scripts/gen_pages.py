"""mkdocs-gen-files hook: mirror projects/ and resources/ into the build.

Those directories live outside docs_dir (docs/) so they aren't served by
MkDocs by default. This script runs at build time and copies their Markdown
files into virtual pages, plus writes an index page for each section — so
new/edited files there show up on the next build with no config change.
"""

import re
from pathlib import Path

import mkdocs_gen_files

REPO_ROOT = Path(__file__).resolve().parent.parent

# projects/ and resources/ link to docs/ with paths like "../../docs/01-.../x.md".
# docs/ *is* the site root once mirrored in, so drop the "docs/" segment.
_DOCS_LINK = re.compile(r"(\((?:\.\./)+)docs/")


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

        title = None
        for line in content.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break
        entries.append((title or rel.stem, dest))
    return entries


project_entries = mirror("projects", "projects")
resource_entries = mirror("resources", "resources")
diagram_entries = mirror("diagrams", "diagrams")

with mkdocs_gen_files.open("projects/index.md", "w") as f:
    f.write("# Capstone Projects\n\n")
    f.write(
        "Ten full project specs — goal, requirements, architecture, API "
        "design, database schema, and a production checklist for each.\n\n"
    )
    for title, dest in project_entries:
        if dest == "projects/index.md":
            continue
        link = dest.removeprefix("projects/")
        f.write(f"- [{title}]({link})\n")

with mkdocs_gen_files.open("resources/index.md", "w") as f:
    f.write("# Resources\n\n")
    f.write("Cheatsheets, exercises, interview questions, and a glossary.\n\n")
    for title, dest in resource_entries:
        if dest == "resources/index.md":
            continue
        link = dest.removeprefix("resources/")
        f.write(f"- [{title}]({link})\n")

with mkdocs_gen_files.open("diagrams/index.md", "w") as f:
    f.write("# Reference Diagrams\n\n")
    f.write("Standalone Mermaid diagrams referenced throughout the handbook.\n\n")
    for title, dest in diagram_entries:
        if dest == "diagrams/index.md":
            continue
        link = dest.removeprefix("diagrams/")
        f.write(f"- [{title}]({link})\n")

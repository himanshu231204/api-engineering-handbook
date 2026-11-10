"""Draft a video script skeleton from a handbook chapter.

The draft seeds the Hook (from the TL;DR "In one line") and the Demo (first real
example block); every other beat quotes its chapter sections inside an HTML
comment for the author to rewrite as spoken prose. A draft is never `reviewed`.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from script_model import BEAT_NAMES  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]

SOURCES = {
    "Why It Matters": ["Why This Matters"],
    "Concept": ["Core Concept", "Mental Model"],
    "How It Works": ["How It Works", "Architecture"],
    "Mistakes": ["Common Mistakes", "Production Considerations"],
    "Recap": ["Key Takeaways"],
}
PROMPTS = {
    "Hook": "0:00-0:30. Open with the one-line promise below, in your own spoken words.",
    "Why It Matters": "0:30-1:30. A concrete problem the viewer has hit.",
    "Concept": "1:30-3:00. Core concept and mental model.",
    "How It Works": "3:00-5:00. Step by step. Add: [scene: DiagramWalk svg=NN-name.svg steps=1-6]",
    "Demo": "5:00-6:30. Say what the commands do; every line must appear in the chapter or examples/.",
    "Mistakes": "6:30-7:30. Common mistakes and production tips.",
    "Recap": "7:30-8:30. Takeaways, then a quiz cue: [scene: Quiz q1=... a1=... q2=... a2=... q3=... a3=...]",
    "Next": "8:30-9:00. Tease the next video in the part.",
}
_FENCE = re.compile(r"```(\w*)\n(.*?)\n```", re.DOTALL)


def _sections(text: str) -> dict[str, str]:
    parts = re.split(r"^## (.+)$", text, flags=re.MULTILINE)
    return {parts[i].strip(): parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}


def _comment(label: str, body: str) -> str:
    return f"<!-- Source: {label}\n{body.replace('-->', '- ->')}\n-->"


def _next_title(chapter: Path, index: int) -> str | None:
    readme = chapter.parent / "README.md"
    if not readme.is_file():
        return None
    for line in readme.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\|\s*(\d+)\s*\|\s*\[?([^\]|]+?)\]?(?:\([^)]*\))?\s*\|", line)
        if m and int(m.group(1)) == index + 1:
            return m.group(2).strip()
    return None


def _demo_block(sections: dict[str, str], text: str) -> str | None:
    scoped = sections.get("Request / Response Example", "")
    for source in (scoped, text):
        for lang, body in _FENCE.findall(source):
            if lang not in ("python", "mermaid"):
                return body
    return None


def draft_script(chapter_path: Path, part: int, index: int, repo_root: Path = REPO_ROOT) -> str:
    text = chapter_path.read_text(encoding="utf-8")
    title_match = re.search(r"^# (.+)$", text, flags=re.MULTILINE)
    title = title_match.group(1).strip() if title_match else chapter_path.stem
    one_line = re.search(r"\*\*In one line:\*\*\s*(.+)", text)
    sections = _sections(text)
    try:
        rel = chapter_path.resolve().relative_to(repo_root).as_posix()
    except ValueError:
        rel = str(chapter_path)

    out = [
        "---",
        f"chapter: {rel}",
        f"part: {part}",
        f"index: {index}",
        f"title: {title}",
        "target_seconds: 420",
        "reviewed: false",
        "---",
        "",
    ]
    for name in BEAT_NAMES:
        out += [f"## {name}", "", f"<!-- {PROMPTS[name]} -->", ""]
        if name == "Hook" and one_line:
            out += [one_line.group(1).replace("`", "").strip(), ""]
        elif name in SOURCES:
            for label in SOURCES[name]:
                if label in sections:
                    out += [_comment(label, sections[label]), ""]
        elif name == "Demo":
            block = _demo_block(sections, text)
            if block:
                out += ["```text", block, "```", ""]
            if "Code Example" in sections:
                out += [_comment("Code Example", sections["Code Example"]), ""]
        elif name == "Next":
            nxt = _next_title(chapter_path, index)
            if nxt:
                out += [f"<!-- Next video in the part: {nxt} -->", ""]
    return "\n".join(out).rstrip() + "\n"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Draft a video script from a chapter")
    parser.add_argument("chapter", type=Path)
    parser.add_argument("--part", type=int, required=True)
    parser.add_argument("--index", type=int, required=True)
    args = parser.parse_args(argv)
    sys.stdout.write(draft_script(args.chapter, args.part, args.index))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

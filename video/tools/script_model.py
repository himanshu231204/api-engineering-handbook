"""Parse a video script (Markdown with frontmatter, beat headings and scene cues)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

BEAT_NAMES = [
    "Hook",
    "Why It Matters",
    "Concept",
    "How It Works",
    "Demo",
    "Mistakes",
    "Recap",
    "Next",
]

WORDS_PER_MINUTE = 150

_CUE_RE = re.compile(r"^\[scene:\s*(\w+)(.*)\]$")
_ARG_RE = re.compile(r'(\w+)=("([^"]*)"|\S+)')
_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)


@dataclass
class Cue:
    scene: str
    args: dict[str, str]
    line: int


@dataclass
class Beat:
    name: str
    narration: str = ""
    cues: list[Cue] = field(default_factory=list)
    code_blocks: list[str] = field(default_factory=list)
    line: int = 0


@dataclass
class Script:
    meta: dict[str, str]
    beats: list[Beat]


def _blank_comments(text: str) -> str:
    """Replace HTML comments with the same number of newlines, keeping line numbers."""
    return _COMMENT_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)


def parse_script(text: str) -> Script:
    lines = _blank_comments(text.replace("\r\n", "\n").replace("\r", "\n")).split("\n")
    meta: dict[str, str] = {}
    start = 0
    if lines and lines[0].strip() == "---":
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
        if end is None:
            raise ValueError("line 1: unclosed frontmatter")
        for i in range(1, end):
            raw = lines[i]
            if not raw.strip():
                continue
            if ":" not in raw:
                raise ValueError(f"line {i + 1}: frontmatter needs 'key: value'")
            key, value = raw.split(":", 1)
            meta[key.strip()] = value.strip()
        start = end + 1

    beats: list[Beat] = []
    current: Beat | None = None
    narration: list[str] = []
    fence: list[str] | None = None

    def finish() -> None:
        if current is not None:
            current.narration = "\n".join(narration).strip()

    for idx in range(start, len(lines)):
        line = lines[idx]
        number = idx + 1
        stripped = line.strip()
        if fence is not None:
            if stripped.startswith("```"):
                assert current is not None
                current.code_blocks.append("\n".join(fence))
                fence = None
            else:
                fence.append(line)
            continue
        if stripped.startswith("## "):
            finish()
            current = Beat(name=stripped[3:].strip(), line=number)
            beats.append(current)
            narration = []
            continue
        if current is None:
            continue
        if stripped.startswith("```"):
            fence = []
            continue
        if stripped.startswith("[scene:"):
            match = _CUE_RE.match(stripped)
            if not match:
                raise ValueError(f"line {number}: malformed scene cue")
            args = {
                k: (v[1:-1] if v.startswith('"') else v)
                for k, v, _ in _ARG_RE.findall(match.group(2))
            }
            current.cues.append(Cue(match.group(1), args, number))
            continue
        narration.append(line)
    if fence is not None:
        raise ValueError("unclosed code fence")
    finish()
    return Script(meta=meta, beats=beats)


def narration_words(script: Script) -> int:
    return sum(len(b.narration.split()) for b in script.beats)


def estimated_seconds(script: Script) -> float:
    return narration_words(script) / WORDS_PER_MINUTE * 60.0

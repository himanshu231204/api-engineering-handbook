"""Split narration into timed caption chunks and render SubRip (.srt)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Caption:
    start: float
    end: float
    text: str


def chunk_narration(text: str, start: float, end: float, max_chars: int = 42) -> list[Caption]:
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    line = ""
    for word in words:
        candidate = f"{line} {word}" if line else word
        if line and len(candidate) > max_chars:
            lines.append(line)
            line = word
        else:
            line = candidate
    lines.append(line)

    total = sum(len(item) for item in lines)
    boundaries = [start]
    acc = 0
    for item in lines[:-1]:
        acc += len(item)
        boundaries.append(start + (end - start) * acc / total)
    boundaries.append(end)
    return [Caption(boundaries[i], boundaries[i + 1], lines[i]) for i in range(len(lines))]


def _timestamp(seconds: float) -> str:
    millis = round(seconds * 1000)
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def build_srt(captions: list[Caption]) -> str:
    entries = [
        f"{i}\n{_timestamp(c.start)} --> {_timestamp(c.end)}\n{c.text}\n"
        for i, c in enumerate(captions, start=1)
    ]
    return "\n".join(entries)

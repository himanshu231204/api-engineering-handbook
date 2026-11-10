"""Turn a parsed script plus beat durations into the JSON the Remotion kit renders."""
from __future__ import annotations

import re

from captions import chunk_narration
from script_model import Beat, Script

_DEFAULT_SCENE = {
    "Hook": "Concept",
    "Why It Matters": "Concept",
    "Concept": "Concept",
    "How It Works": "Concept",
    "Demo": "Terminal",
    "Mistakes": "Mistakes",
    "Recap": "Recap",
    "Next": "Concept",
}


def _sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]


def _default_cue(beat: Beat) -> tuple[str, dict[str, str]]:
    scene = _DEFAULT_SCENE.get(beat.name, "Concept")
    sentences = _sentences(beat.narration)
    if scene == "Terminal":
        if beat.code_blocks:
            return "Terminal", {"lines": "|".join(beat.code_blocks[0].split("\n"))}
        scene = "Concept"
    if scene in ("Mistakes", "Recap"):
        return scene, {"items": "|".join(sentences[:4])}
    return "Concept", {"heading": beat.name, "body": sentences[0] if sentences else ""}


def build_timeline(
    script: Script,
    durations: dict[str, float],
    fps: int = 30,
    audio: dict[str, str] | None = None,
) -> dict:
    audio = audio or {}
    beats = []
    position = 0
    for beat in script.beats:
        frames = max(1, round(durations[beat.name] * fps))
        if beat.cues:
            raw = [(c.scene, c.args) for c in beat.cues]
        else:
            raw = [_default_cue(beat)]
        base, extra = divmod(frames, len(raw))
        cues = []
        cursor = position
        for i, (scene, args) in enumerate(raw):
            length = base + (extra if i == len(raw) - 1 else 0)
            cues.append({"scene": scene, "args": args, "startFrame": cursor, "frames": length})
            cursor += length
        captions = [
            {
                "startFrame": round(c.start * fps),
                "endFrame": round(c.end * fps),
                "text": c.text,
            }
            for c in chunk_narration(beat.narration, position / fps, (position + frames) / fps)
        ]
        beats.append(
            {
                "name": beat.name,
                "startFrame": position,
                "frames": frames,
                "audio": audio.get(beat.name),
                "cues": cues,
                "captions": captions,
            }
        )
        position += frames
    return {
        "fps": fps,
        "width": 1920,
        "height": 1080,
        "title": script.meta.get("title", ""),
        "part": int(script.meta.get("part", 0) or 0),
        "index": int(script.meta.get("index", 0) or 0),
        "beats": beats,
        "totalFrames": position,
    }


_CHAPTER_LABELS = {
    "Hook": "Intro",
    "Why It Matters": "Why it matters",
    "Concept": "The core concept",
    "How It Works": "How it works",
    "Demo": "Demo",
    "Mistakes": "Common mistakes",
    "Recap": "Recap and quiz",
    "Next": "What's next",
}
_MIN_CHAPTER_SECONDS = 10


def _stamp(seconds: float) -> str:
    total = round(seconds)
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"


def build_chapters(timeline: dict) -> str:
    """YouTube chapter lines. Starts at 00:00, every chapter >= 10 s, else empty.

    Beats shorter than 10 s are folded into the following beat; a short final
    remainder is folded into the previous chapter. Fewer than 3 chapters gives "".
    """
    fps = timeline["fps"]
    chapters: list[list] = []  # [start_seconds, label, duration_seconds]
    carry = None
    for beat in timeline["beats"]:
        duration = beat["frames"] / fps
        if carry is None:
            carry = [beat["startFrame"] / fps, _CHAPTER_LABELS.get(beat["name"], beat["name"]), 0.0]
        carry[2] += duration
        if carry[2] >= _MIN_CHAPTER_SECONDS:
            chapters.append(carry)
            carry = None
    if carry is not None and chapters:
        chapters[-1][2] += carry[2]
    if len(chapters) < 3:
        return ""
    return "\n".join(f"{_stamp(start)} {label}" for start, label, _ in chapters) + "\n"

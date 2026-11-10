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

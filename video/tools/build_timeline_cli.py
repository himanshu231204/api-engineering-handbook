"""Build timeline.json, captions.srt and narration audio for a script."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Mapping

sys.path.insert(0, str(Path(__file__).resolve().parent))

from captions import Caption, build_srt  # noqa: E402
from script_model import parse_script  # noqa: E402
from timeline import build_chapters, build_timeline  # noqa: E402
from tts import audio_name, beat_durations, get_provider  # noqa: E402


def build_assets(script_path: Path, out_dir: Path, env: Mapping[str, str]) -> dict:
    script = parse_script(script_path.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    provider = get_provider(env)
    durations = beat_durations(script, provider, out_dir / "audio")
    audio = (
        {beat.name: audio_name(i, beat.name) for i, beat in enumerate(script.beats)}
        if provider is not None
        else {}
    )
    timeline = build_timeline(script, durations, audio=audio)
    fps = timeline["fps"]
    captions = [
        Caption(c["startFrame"] / fps, c["endFrame"] / fps, c["text"])
        for beat in timeline["beats"]
        for c in beat["captions"]
    ]
    (out_dir / "timeline.json").write_text(json.dumps({"timeline": timeline}, ensure_ascii=False, indent=1), encoding="utf-8")
    (out_dir / "captions.srt").write_text(build_srt(captions), encoding="utf-8")
    (out_dir / "chapters.txt").write_text(build_chapters(timeline), encoding="utf-8")
    return timeline


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("script", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    timeline = build_assets(args.script, args.out_dir, os.environ)
    print(f"timeline: {timeline['totalFrames'] / timeline['fps']:.1f}s, {len(timeline['beats'])} beats")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

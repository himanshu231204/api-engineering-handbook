"""Narration: provider adapter, duration estimates, per-beat audio."""
from __future__ import annotations

import json
import subprocess
import urllib.request
from pathlib import Path
from typing import Mapping, Protocol

from script_model import WORDS_PER_MINUTE, Script

PAUSE_SECONDS = 0.4


class TTSProvider(Protocol):
    def synthesize(self, text: str, out: Path) -> float:
        """Write audio for `text` to `out`; return its duration in seconds."""


class OpenAICompatibleTTS:
    def __init__(self, base_url: str, api_key: str, model: str, voice: str) -> None:
        self.base_url, self.api_key, self.model, self.voice = base_url.rstrip("/"), api_key, model, voice

    def synthesize(self, text: str, out: Path) -> float:
        body = json.dumps({"model": self.model, "voice": self.voice, "input": text}).encode()
        request = urllib.request.Request(
            f"{self.base_url}/audio/speech",
            data=body,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            out.write_bytes(response.read())
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(out)],
            check=True,
            capture_output=True,
            text=True,
        )
        return float(probe.stdout.strip())


def get_provider(env: Mapping[str, str]) -> TTSProvider | None:
    name = env.get("VIDEO_TTS_PROVIDER", "").strip().lower()
    if name in ("", "none"):
        return None
    if name == "openai-compatible":
        missing = [
            k
            for k in ("VIDEO_TTS_BASE_URL", "VIDEO_TTS_API_KEY", "VIDEO_TTS_MODEL", "VIDEO_TTS_VOICE")
            if not env.get(k)
        ]
        if missing:
            raise ValueError(f"openai-compatible TTS needs env vars: {', '.join(missing)}")
        return OpenAICompatibleTTS(
            env["VIDEO_TTS_BASE_URL"], env["VIDEO_TTS_API_KEY"], env["VIDEO_TTS_MODEL"], env["VIDEO_TTS_VOICE"]
        )
    raise ValueError(f"unknown VIDEO_TTS_PROVIDER '{name}'")


def estimate_seconds(text: str) -> float:
    return len(text.split()) / WORDS_PER_MINUTE * 60.0


def audio_name(index: int, beat_name: str) -> str:
    return f"{index:02d}-{beat_name.lower().replace(' ', '-')}.mp3"


def beat_durations(script: Script, provider: TTSProvider | None, out_dir: Path) -> dict[str, float]:
    out_dir.mkdir(parents=True, exist_ok=True)
    created: list[Path] = []
    durations: dict[str, float] = {}
    try:
        for index, beat in enumerate(script.beats):
            if provider is None:
                durations[beat.name] = estimate_seconds(beat.narration) + PAUSE_SECONDS
                continue
            target = out_dir / audio_name(index, beat.name)
            created.append(target)
            durations[beat.name] = provider.synthesize(beat.narration, target) + PAUSE_SECONDS
    except Exception:
        for path in created:
            path.unlink(missing_ok=True)
        raise
    return durations

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


def _probe_duration(path: Path) -> float:
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(probe.stdout.strip())


class KokoroTTS:
    """Local, free narration with Kokoro (https://github.com/thewh1teagle/kokoro-onnx).

    Runs `kokoro_say.py` in a separate virtualenv (VIDEO_KOKORO_PYTHON) so these tools
    stay stdlib-only; converts the wav to mp3 with ffmpeg.
    """

    def __init__(self, model_dir: Path, python: str, voice: str, speed: float) -> None:
        self.model_dir, self.python, self.voice, self.speed = model_dir, python, voice, speed

    def synthesize(self, text: str, out: Path) -> float:
        model = self.model_dir / "kokoro-v1.0.onnx"
        voices = self.model_dir / "voices-v1.0.bin"
        for needed in (model, voices):
            if not needed.is_file():
                raise FileNotFoundError(
                    f"Kokoro file missing: {needed} (see video/README.md, 'Narration')"
                )
        wav = out.with_suffix(".wav")
        helper = Path(__file__).resolve().parent / "kokoro_say.py"
        try:
            subprocess.run(
                [self.python, str(helper), str(model), str(voices), self.voice, str(self.speed), str(wav)],
                input=text,
                text=True,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav), "-codec:a", "libmp3lame", "-q:a", "2", str(out)],
                check=True,
            )
        finally:
            wav.unlink(missing_ok=True)
        return _probe_duration(out)


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
        return _probe_duration(out)


def get_provider(env: Mapping[str, str]) -> TTSProvider | None:
    name = env.get("VIDEO_TTS_PROVIDER", "").strip().lower()
    if name in ("", "none"):
        return None
    if name == "kokoro":
        root = Path(__file__).resolve().parents[1]
        return KokoroTTS(
            Path(env.get("VIDEO_KOKORO_DIR", str(root / ".cache" / "models"))),
            env.get("VIDEO_KOKORO_PYTHON", str(root / ".cache" / "tts" / "bin" / "python")),
            env.get("VIDEO_TTS_VOICE", "am_michael"),
            float(env.get("VIDEO_KOKORO_SPEED", "1.03")),
        )
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

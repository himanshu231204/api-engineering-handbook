import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from script_model import BEAT_NAMES, parse_script  # noqa: E402
from tts import beat_durations, estimate_seconds, get_provider  # noqa: E402


def script():
    text = "---\ntitle: T\n---\n" + "\n".join(f"## {n}\n\n{'w ' * 150}\n" for n in BEAT_NAMES)
    return parse_script(text)


class FakeProvider:
    def __init__(self, fail_on=None):
        self.calls = 0
        self.fail_on = fail_on

    def synthesize(self, text, out):
        self.calls += 1
        if self.fail_on == self.calls:
            raise RuntimeError("tts down")
        Path(out).write_bytes(b"mp3")
        return 2.0


class TTSTests(unittest.TestCase):
    def test_get_provider_none_when_unset(self):
        self.assertIsNone(get_provider({}))
        self.assertIsNone(get_provider({"VIDEO_TTS_PROVIDER": "none"}))

    def test_unknown_provider_raises(self):
        with self.assertRaises(ValueError):
            get_provider({"VIDEO_TTS_PROVIDER": "carrier-pigeon"})

    def test_openai_compatible_requires_settings(self):
        with self.assertRaises(ValueError):
            get_provider({"VIDEO_TTS_PROVIDER": "openai-compatible"})

    def test_openai_compatible_builds_without_network(self):
        env = {
            "VIDEO_TTS_PROVIDER": "openai-compatible",
            "VIDEO_TTS_BASE_URL": "https://example.invalid/v1",
            "VIDEO_TTS_API_KEY": "test-key",
            "VIDEO_TTS_MODEL": "m",
            "VIDEO_TTS_VOICE": "v",
        }
        self.assertTrue(hasattr(get_provider(env), "synthesize"))

    def test_estimate_seconds_matches_150wpm(self):
        self.assertAlmostEqual(estimate_seconds("w " * 150), 60.0)

    def test_beat_durations_without_provider_uses_estimate_plus_pause(self):
        with tempfile.TemporaryDirectory() as d:
            result = beat_durations(script(), None, Path(d))
            self.assertEqual(list(result), BEAT_NAMES)
            for v in result.values():
                self.assertAlmostEqual(v, 60.4)
            self.assertEqual(list(Path(d).glob("*.mp3")), [])

    def test_beat_durations_with_provider_writes_audio(self):
        with tempfile.TemporaryDirectory() as d:
            result = beat_durations(script(), FakeProvider(), Path(d))
            self.assertAlmostEqual(result["Hook"], 2.4)
            self.assertEqual(len(list(Path(d).glob("*.mp3"))), 8)

    def test_failure_midway_removes_partial_audio(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(RuntimeError):
                beat_durations(script(), FakeProvider(fail_on=3), Path(d))
            self.assertEqual(list(Path(d).glob("*.mp3")), [])


if __name__ == "__main__":
    unittest.main()

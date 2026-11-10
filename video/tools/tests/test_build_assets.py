import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from build_timeline_cli import build_assets  # noqa: E402
from script_model import BEAT_NAMES  # noqa: E402


def script_text() -> str:
    beats = "\n".join(f"## {n}\n\n{'word ' * 120}\n" for n in BEAT_NAMES)
    return f"---\nchapter: x.md\npart: 1\nindex: 5\ntitle: DNS\ntarget_seconds: 420\n---\n\n{beats}"


class BuildAssetsTests(unittest.TestCase):
    def test_writes_timeline_and_srt_without_provider(self):
        with tempfile.TemporaryDirectory() as d:
            script = Path(d) / "s.md"
            script.write_text(script_text())
            out = Path(d) / "out"
            tl = build_assets(script, out, {})
            self.assertEqual(json.loads((out / "timeline.json").read_text())["timeline"]["totalFrames"], tl["totalFrames"])
            srt = (out / "captions.srt").read_text()
            last = re.findall(r"--> (\d\d):(\d\d):(\d\d),(\d\d\d)", srt)[-1]
            end = int(last[0]) * 3600 + int(last[1]) * 60 + int(last[2]) + int(last[3]) / 1000
            self.assertAlmostEqual(end, tl["totalFrames"] / tl["fps"], delta=0.5)
            for line in srt.splitlines():
                if "-->" not in line and not line.strip().isdigit() and line.strip():
                    self.assertLessEqual(len(line), 42)
            self.assertEqual(list((out / "audio").glob("*.mp3")) if (out / "audio").exists() else [], [])


if __name__ == "__main__":
    unittest.main()

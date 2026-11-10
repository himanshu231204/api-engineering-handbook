import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from script_model import BEAT_NAMES, parse_script  # noqa: E402
from timeline import build_timeline  # noqa: E402


def make(bodies=None):
    bodies = bodies or {}
    text = "---\ntitle: DNS\npart: 1\nindex: 5\n---\n" + "\n".join(
        f"## {n}\n\n{bodies.get(n, 'First sentence here. Second one. Third one. Fourth. Fifth.')}\n"
        for n in BEAT_NAMES
    )
    return parse_script(text)


DUR = {n: 10.0 for n in BEAT_NAMES}


class TimelineTests(unittest.TestCase):
    def test_beats_contiguous_and_total_frames_sum(self):
        tl = build_timeline(make(), DUR)
        pos = 0
        for beat in tl["beats"]:
            self.assertEqual(beat["startFrame"], pos)
            pos += beat["frames"]
        self.assertEqual(tl["totalFrames"], pos)
        self.assertEqual(pos, 8 * 300)
        self.assertEqual((tl["fps"], tl["width"], tl["height"]), (30, 1920, 1080))
        self.assertEqual((tl["title"], tl["part"], tl["index"]), ("DNS", 1, 5))

    def test_cues_split_beat_frames_equally(self):
        body = "Words here.\n[scene: Concept heading=A body=B]\n[scene: Concept heading=C body=D]\n[scene: Concept heading=E body=F]\n"
        tl = build_timeline(make({"Concept": body}), DUR)
        beat = next(b for b in tl["beats"] if b["name"] == "Concept")
        self.assertEqual(len(beat["cues"]), 3)
        self.assertEqual(sum(c["frames"] for c in beat["cues"]), beat["frames"])
        self.assertEqual(beat["cues"][0]["startFrame"], beat["startFrame"])
        for a, b in zip(beat["cues"], beat["cues"][1:]):
            self.assertEqual(a["startFrame"] + a["frames"], b["startFrame"])

    def test_default_scene_for_beat_without_cues(self):
        tl = build_timeline(make(), DUR)
        scenes = {b["name"]: b["cues"][0]["scene"] for b in tl["beats"]}
        self.assertEqual(scenes["Hook"], "Concept")
        self.assertEqual(scenes["Recap"], "Recap")
        self.assertEqual(scenes["Mistakes"], "Mistakes")
        self.assertEqual(scenes["How It Works"], "Concept")

    def test_demo_default_terminal_uses_first_code_block(self):
        body = "Say.\n\n```text\ndig a.com\n+short\n```\n"
        tl = build_timeline(make({"Demo": body}), DUR)
        cue = next(b for b in tl["beats"] if b["name"] == "Demo")["cues"][0]
        self.assertEqual(cue["scene"], "Terminal")
        self.assertEqual(cue["args"]["lines"], "dig a.com|+short")

    def test_audio_none_when_no_provider(self):
        tl = build_timeline(make(), DUR)
        self.assertTrue(all(b["audio"] is None for b in tl["beats"]))

    def test_audio_mapping_is_used(self):
        tl = build_timeline(make(), DUR, audio={"Hook": "00-hook.mp3"})
        self.assertEqual(tl["beats"][0]["audio"], "00-hook.mp3")
        self.assertIsNone(tl["beats"][1]["audio"])

    def test_captions_are_absolute_frames_inside_their_beat(self):
        tl = build_timeline(make(), DUR)
        for beat in tl["beats"]:
            self.assertTrue(beat["captions"])
            end = beat["startFrame"] + beat["frames"]
            for c in beat["captions"]:
                self.assertGreaterEqual(c["startFrame"], beat["startFrame"])
                self.assertLessEqual(c["endFrame"], end)
                self.assertLess(c["startFrame"], c["endFrame"])


if __name__ == "__main__":
    unittest.main()

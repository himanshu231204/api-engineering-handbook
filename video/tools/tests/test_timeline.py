import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from script_model import BEAT_NAMES, parse_script  # noqa: E402
from timeline import build_chapters, build_timeline  # noqa: E402


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



class ChapterTests(unittest.TestCase):
    def test_chapters_start_at_zero_and_use_friendly_labels(self):
        tl = build_timeline(make(), {n: 20.0 for n in BEAT_NAMES})
        lines = build_chapters(tl).splitlines()
        self.assertEqual(lines[0], "00:00 Intro")
        self.assertEqual(lines[1], "00:20 Why it matters")

    def test_short_beat_is_merged_into_previous_chapter(self):
        durations = {n: 20.0 for n in BEAT_NAMES} | {"Next": 6.0}
        text = build_chapters(build_timeline(make(), durations))
        self.assertNotIn("What's next", text)
        self.assertEqual(len(text.splitlines()), 7)

    def test_every_chapter_is_at_least_ten_seconds(self):
        durations = {n: 8.0 for n in BEAT_NAMES} | {"Concept": 30.0}
        text = build_chapters(build_timeline(make(), durations))
        stamps = [int(l[:2]) * 60 + int(l[3:5]) for l in text.splitlines()]
        total = 8 * 7 + 30 - 8 + 8  # sum of durations
        bounds = stamps + [round(sum(durations.values()))]
        for a, b in zip(bounds, bounds[1:]):
            self.assertGreaterEqual(b - a, 10)

    def test_hour_long_timestamps_use_h_mm_ss(self):
        durations = {n: 600.0 for n in BEAT_NAMES}
        text = build_chapters(build_timeline(make(), durations))
        self.assertIn("1:00:00", text)

    def test_at_least_three_chapters_or_empty(self):
        tl = build_timeline(make(), {n: 11.0 for n in BEAT_NAMES} | {"Hook": 5.0})
        self.assertGreaterEqual(len(build_chapters(tl).splitlines()), 3)


if __name__ == "__main__":
    unittest.main()

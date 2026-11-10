import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from script_model import BEAT_NAMES, Cue, estimated_seconds, narration_words, parse_script  # noqa: E402


def sample(beat_body: dict[str, str] | None = None) -> str:
    beat_body = beat_body or {}
    parts = [
        "---\nchapter: docs/x.md\npart: 1\nindex: 5\ntitle: DNS\ntarget_seconds: 420\nreviewed: false\n---\n"
    ]
    for name in BEAT_NAMES:
        parts.append(f"## {name}\n\n{beat_body.get(name, 'one two three four five.')}\n")
    return "\n".join(parts)


class ParseScriptTests(unittest.TestCase):
    def test_parse_basic_script_has_eight_beats_in_order(self):
        s = parse_script(sample())
        self.assertEqual([b.name for b in s.beats], BEAT_NAMES)
        self.assertEqual(s.meta["title"], "DNS")
        self.assertEqual(s.meta["part"], "1")

    def test_crlf_input_parses_identically(self):
        text = sample({"Demo": "Say this.\n\n```text\ndig a.com\n```\n"})
        self.assertEqual(parse_script(text), parse_script(text.replace("\n", "\r\n")))

    def test_cue_removed_from_narration_and_args_parsed(self):
        body = "Walk through it.\n[scene: DiagramWalk svg=01-dns-resolution.svg steps=1-6]\nDone."
        s = parse_script(sample({"How It Works": body}))
        beat = s.beats[BEAT_NAMES.index("How It Works")]
        self.assertEqual(len(beat.cues), 1)
        cue = beat.cues[0]
        self.assertEqual(cue.scene, "DiagramWalk")
        self.assertEqual(cue.args, {"svg": "01-dns-resolution.svg", "steps": "1-6"})
        self.assertGreater(cue.line, 1)
        self.assertNotIn("[scene", beat.narration)
        self.assertIn("Walk through it.", beat.narration)

    def test_code_block_not_counted_as_narration(self):
        s = parse_script(sample({"Demo": "Say this.\n\n```text\ndig a.com +short\n```\n"}))
        beat = s.beats[BEAT_NAMES.index("Demo")]
        self.assertEqual(beat.code_blocks, ["dig a.com +short"])
        self.assertNotIn("dig", beat.narration)

    def test_unicode_and_backticks_counted_as_words(self):
        s = parse_script(sample({b: "x" for b in BEAT_NAMES} | {"Hook": "résumé `dig` 日本語 ok"}))
        hook = s.beats[0]
        self.assertEqual(len(hook.narration.split()), 4)

    def test_estimated_seconds_is_words_over_150_times_60(self):
        s = parse_script(sample({b: "w " * 150 for b in BEAT_NAMES}))
        self.assertEqual(narration_words(s), 150 * 8)
        self.assertAlmostEqual(estimated_seconds(s), 8 * 60.0)

    def test_html_comment_not_narration(self):
        s = parse_script(sample({"Hook": "<!-- prompt -->\nreal words here"}))
        self.assertEqual(s.beats[0].narration.strip(), "real words here")

    def test_unclosed_frontmatter_raises_with_line(self):
        with self.assertRaises(ValueError) as cm:
            parse_script("---\ntitle: x\n## Hook\nhi\n")
        self.assertIn("line", str(cm.exception))


if __name__ == "__main__":
    unittest.main()

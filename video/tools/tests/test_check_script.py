import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from check_script import check_script  # noqa: E402
from script_model import BEAT_NAMES  # noqa: E402

SCENES = ["Title", "Concept", "DiagramWalk", "Terminal", "CodeReveal", "Mistakes", "Recap", "Quiz"]
FM = "chapter: docs/01-api-foundations/dns.md\npart: 1\nindex: 5\ntitle: DNS\ntarget_seconds: 420\nreviewed: true"


def filler(n: int) -> str:
    return " ".join(["word"] * n) + "."


def build(words_per_beat=110, bodies=None, fm=FM, beats=None) -> str:
    bodies = bodies or {}
    out = [f"---\n{fm}\n---\n"]
    for name in beats or BEAT_NAMES:
        out.append(f"## {name}\n\n{bodies.get(name, filler(words_per_beat))}\n")
    return "\n".join(out)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "docs/01-api-foundations").mkdir(parents=True)
        (self.root / "docs/01-api-foundations/dns.md").write_text("# DNS\n\n```text\ndig example.com\n```\n")
        (self.root / "examples/a").mkdir(parents=True)
        (self.root / "examples/a/x.py").write_text("import socket\nsocket.gethostbyname(name)\n")
        (self.root / "docs/assets/diagrams").mkdir(parents=True)
        (self.root / "docs/assets/diagrams/01-dns-resolution.svg").write_text("<svg/>")
        kit = self.root / "video/kit"
        (kit / "diagram_steps").mkdir(parents=True)
        (kit / "scene_names.json").write_text(json.dumps(SCENES))
        steps = [{"n": i, "label": f"s{i}", "x": 0, "y": 0, "w": 10, "h": 10} for i in range(1, 7)]
        (kit / "diagram_steps/01-dns-resolution.json").write_text(
            json.dumps({"width": 880, "height": 500, "steps": steps})
        )
        self.script = self.root / "video/scripts/01-api-foundations/dns.md"
        self.script.parent.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def run_check(self, text: str) -> list[str]:
        self.script.write_text(text)
        return check_script(self.script, self.root)


class CheckScriptTests(Base):
    def test_valid_script_passes(self):
        self.assertEqual(self.run_check(build()), [])

    def test_missing_chapter_file_fails(self):
        errs = self.run_check(build(fm=FM.replace("dns.md", "nope.md")))
        self.assertTrue(any("chapter" in e for e in errs), errs)

    def test_missing_frontmatter_key_fails(self):
        errs = self.run_check(build(fm=FM.replace("part: 1\n", "")))
        self.assertTrue(any("part" in e for e in errs), errs)

    def test_misspelled_beat_heading_fails(self):
        names = [n if n != "Concept" else "Concpet" for n in BEAT_NAMES]
        errs = self.run_check(build(beats=names))
        self.assertTrue(any("Concpet" in e or "Concept" in e for e in errs), errs)

    def test_duplicate_beat_fails(self):
        errs = self.run_check(build(beats=BEAT_NAMES + ["Hook"]))
        self.assertTrue(errs)

    def test_empty_beat_narration_fails(self):
        errs = self.run_check(build(bodies={"Concept": ""}))
        self.assertTrue(any("Concept" in e and "empty" in e for e in errs), errs)

    def test_word_count_below_750_fails(self):
        errs = self.run_check(build(words_per_beat=50))
        self.assertTrue(any("750" in e for e in errs), errs)

    def test_word_count_above_1500_fails(self):
        errs = self.run_check(build(words_per_beat=250))
        self.assertTrue(any("1500" in e for e in errs), errs)

    def test_unknown_scene_fails_with_line_number(self):
        body = filler(110) + "\n[scene: Confetti]\n"
        errs = self.run_check(build(bodies={"Concept": body}))
        self.assertTrue(any("Confetti" in e and ":" in e for e in errs), errs)
        self.assertTrue(any(f"{self.script}:" in e for e in errs), errs)

    def test_missing_svg_fails(self):
        body = filler(110) + "\n[scene: DiagramWalk svg=nope.svg steps=1-2]\n"
        errs = self.run_check(build(bodies={"How It Works": body}))
        self.assertTrue(any("nope.svg" in e for e in errs), errs)

    def test_steps_beyond_sidecar_count_fails(self):
        body = filler(110) + "\n[scene: DiagramWalk svg=01-dns-resolution.svg steps=1-9]\n"
        errs = self.run_check(build(bodies={"How It Works": body}))
        self.assertTrue(any("steps" in e for e in errs), errs)

    def test_demo_code_line_not_in_chapter_or_examples_fails(self):
        body = filler(110) + "\n```text\ndig invented.example +short\n```\n"
        errs = self.run_check(build(bodies={"Demo": body}))
        self.assertTrue(any("invented.example" in e for e in errs), errs)

    def test_demo_code_line_present_in_chapter_passes(self):
        body = filler(110) + "\n```text\ndig example.com\n```\n"
        self.assertEqual(self.run_check(build(bodies={"Demo": body})), [])

    def test_demo_code_line_present_in_examples_passes(self):
        body = filler(110) + "\n```python\nsocket.gethostbyname(name)\n```\n"
        self.assertEqual(self.run_check(build(bodies={"Demo": body})), [])

    def test_todo_placeholder_fails(self):
        errs = self.run_check(build(bodies={"Hook": filler(110) + " TODO fix"}))
        self.assertTrue(any("TODO" in e for e in errs), errs)

    def test_secret_like_string_fails(self):
        errs = self.run_check(build(bodies={"Hook": filler(110) + " sk-" + "a" * 24}))
        self.assertTrue(any("secret" in e.lower() for e in errs), errs)

    def test_crlf_script_passes(self):
        self.assertEqual(self.run_check(build().replace("\n", "\r\n")), [])


if __name__ == "__main__":
    unittest.main()

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from draft_script import draft_script  # noqa: E402
from script_model import BEAT_NAMES, parse_script  # noqa: E402

REPO = Path(__file__).resolve().parents[3]

CHAPTER = """# Widgets

> [!TIP]
> **In one line:** Widgets turn names into numbers.
>
> **In plain English:** Like a phone book.

## Why This Matters

Widgets break in production.

## Core Concept

A widget is a thing.

## Mental Model

Think of a phone book.

## How It Works

First this, then that.

## Architecture

```mermaid
graph TD
  A --> B
```

## Request / Response Example

```text
GET /widgets
200 OK
```

## Code Example

```python
print("hi")
```

## Common Mistakes

Forgetting widgets.

## Key Takeaways

- Widgets matter.
"""


def make_chapter(text: str = CHAPTER) -> tuple[tempfile.TemporaryDirectory, Path]:
    tmp = tempfile.TemporaryDirectory()
    path = Path(tmp.name) / "widgets.md"
    path.write_text(text)
    return tmp, path


class DraftScriptTests(unittest.TestCase):
    def test_draft_uses_tldr_one_line_as_hook_source(self):
        tmp, path = make_chapter()
        with tmp:
            script = parse_script(draft_script(path, part=3, index=7))
        self.assertIn("Widgets turn names into numbers.", script.beats[0].narration)

    def test_draft_has_all_eight_beats_in_order(self):
        tmp, path = make_chapter()
        with tmp:
            script = parse_script(draft_script(path, part=3, index=7))
        self.assertEqual([b.name for b in script.beats], BEAT_NAMES)
        self.assertEqual(script.meta["title"], "Widgets")
        self.assertEqual((script.meta["part"], script.meta["index"]), ("3", "7"))

    def test_draft_demo_uses_first_non_python_code_block(self):
        tmp, path = make_chapter()
        with tmp:
            script = parse_script(draft_script(path, part=3, index=7))
        demo = script.beats[BEAT_NAMES.index("Demo")]
        self.assertEqual(demo.code_blocks, ["GET /widgets\n200 OK"])

    def test_draft_marks_reviewed_false(self):
        tmp, path = make_chapter()
        with tmp:
            script = parse_script(draft_script(path, part=3, index=7))
        self.assertEqual(script.meta["reviewed"], "false")

    def test_draft_quotes_source_sections_as_comments_not_narration(self):
        tmp, path = make_chapter()
        with tmp:
            text = draft_script(path, part=3, index=7)
            script = parse_script(text)
        self.assertIn("Widgets break in production.", text)
        why = script.beats[BEAT_NAMES.index("Why It Matters")]
        self.assertEqual(why.narration, "")

    def test_draft_for_every_part1_chapter_parses(self):
        chapters = sorted(p for p in (REPO / "docs/01-api-foundations").glob("*.md") if p.name != "README.md")
        self.assertEqual(len(chapters), 11)
        for i, chapter in enumerate(chapters, start=1):
            script = parse_script(draft_script(chapter, part=1, index=i))
            self.assertEqual([b.name for b in script.beats], BEAT_NAMES, chapter.name)
            self.assertTrue(script.beats[0].narration.strip(), f"{chapter.name} hook is empty")


if __name__ == "__main__":
    unittest.main()

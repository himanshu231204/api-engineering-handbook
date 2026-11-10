#!/usr/bin/env python3
"""Regression tests for scripts/check_chapters.py (stdlib only). Run: python3 scripts/test_check_chapters.py"""

import importlib.util
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("check_chapters", HERE / "check_chapters.py")
cc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cc)

FENCE_CASES = [
    ("plain fence", "```py\nx\n```\n", False),
    ("four-backtick block wrapping a three-backtick line", "````md\n```py\nx\n```\n````\n", False),
    ("four-space literal marker inside a top-level fence", "```text\n    ```\nstill code\n```\n", False),
    ("one-space-indented top-level opener, four-space literal marker", " ```text\n    ```\ncode\n ```\n", False),
    ("three-space-indented top-level opener, four-space literal marker", "   ```text\n    ```\ncode\n   ```\n", False),
    ("fence inside a list item (four-space indent)", "1. step\n\n    ```py\n    x\n    ```\n", False),
    ("deeper nested list fence with a deeper literal marker", "- a\n  - b\n\n        ```py\n            ```\n        ```\n", False),
    ("unclosed backtick fence", "```py\nx\n", True),
    ("unclosed tilde fence", "~~~\nx\n", True),
    ("tilde marker does not close a backtick fence", "```\nx\n~~~\n", True),
    ("indented opener left unclosed", " ```py\nx\n", True),
]


class FenceParser(unittest.TestCase):
    def test_cases(self):
        for name, text, unclosed in FENCE_CASES:
            with self.subTest(name):
                self.assertIs(cc.has_unclosed_fence(text), unclosed)


class QuizCheck(unittest.TestCase):
    def check(self, text: str) -> list[str]:
        d = Path(tempfile.mkdtemp()) / "06-x"
        d.mkdir()
        path = d / "c.md"
        path.write_text(text, encoding="utf-8")
        return cc.check(path)[0]

    def test_details_elsewhere_do_not_count_as_a_quiz(self):
        three = "".join(f'<details markdown="1">\n<summary>{i}. q</summary>\n\na\n\n</details>\n\n' for i in (1, 2, 3))
        text = "# T\n\n> [!TIP]\n> **In one line:** x\n>\n> **In plain English:** y\n>\n> **You'll be able to:** z\n\n" + three + "### Check Yourself\n\nnothing\n"
        self.assertTrue(any("Check Yourself" in e for e in self.check(text)))


if __name__ == "__main__":
    unittest.main(verbosity=1)

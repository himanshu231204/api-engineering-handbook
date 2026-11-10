import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from captions import Caption, build_srt, chunk_narration  # noqa: E402


class CaptionTests(unittest.TestCase):
    def test_chunks_respect_max_chars(self):
        text = "DNS turns a name into an IP address through a cached chain of servers and TTL controls reuse."
        chunks = chunk_narration(text, 0.0, 10.0, max_chars=42)
        self.assertGreater(len(chunks), 1)
        for c in chunks:
            self.assertLessEqual(len(c.text), 42, c.text)

    def test_chunks_cover_range_contiguously(self):
        chunks = chunk_narration("one two three four five six seven eight nine ten " * 4, 2.0, 12.5, max_chars=20)
        self.assertEqual(chunks[0].start, 2.0)
        self.assertEqual(chunks[-1].end, 12.5)
        for a, b in zip(chunks, chunks[1:]):
            self.assertEqual(a.end, b.start)

    def test_unicode_text_chunks_and_srt_roundtrip(self):
        long_word = "x" * 60
        text = f"résumé 日本語 {long_word} café ok"
        chunks = chunk_narration(text, 0.0, 4.0, max_chars=42)
        joined = " ".join(c.text for c in chunks)
        self.assertEqual(joined.split(), text.split())
        srt = build_srt(chunks)
        self.assertIn("résumé", srt)
        self.assertIn(long_word, srt)

    def test_srt_timestamp_format(self):
        srt = build_srt([Caption(3725.5, 3726.0, "hello")])
        self.assertEqual(srt, "1\n01:02:05,500 --> 01:02:06,000\nhello\n")

    def test_srt_numbers_entries_and_separates_with_blank_line(self):
        srt = build_srt([Caption(0, 1, "a"), Caption(1, 2, "b")])
        self.assertEqual(srt, "1\n00:00:00,000 --> 00:00:01,000\na\n\n2\n00:00:01,000 --> 00:00:02,000\nb\n")

    def test_empty_text_gives_no_chunks(self):
        self.assertEqual(chunk_narration("   ", 0.0, 1.0), [])


if __name__ == "__main__":
    unittest.main()

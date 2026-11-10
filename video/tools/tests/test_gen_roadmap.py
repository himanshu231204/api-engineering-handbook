import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import gen_roadmap as g  # noqa: E402

REPO = Path(__file__).resolve().parents[3]

README_1 = """# Part 1 — API Foundations

| # | Chapter | Status |
|---|---|---|
| 1 | [How the Internet Works](how-the-internet-works.md) | ✅ Written |
| 2 | [DNS](dns.md) | ✅ Written |
| 3 | Future Chapter | 🚧 Planned |
"""
README_20 = """# Part 20 — Capstone Projects

| # | Project | Builds On | Status |
|---|---|---|---|
| 1 | [CRUD API](../../projects/01-crud-api/README.md) | Parts 1–3 | ✅ Spec written |
"""


def make_repo(tmp: Path) -> Path:
    (tmp / "docs/01-api-foundations").mkdir(parents=True)
    (tmp / "docs/01-api-foundations/README.md").write_text(README_1)
    (tmp / "docs/01-api-foundations/dns.md").write_text("# DNS\n")
    (tmp / "docs/01-api-foundations/how-the-internet-works.md").write_text("# H\n")
    (tmp / "docs/20-capstone-projects").mkdir(parents=True)
    (tmp / "docs/20-capstone-projects/README.md").write_text(README_20)
    (tmp / "projects/01-crud-api").mkdir(parents=True)
    (tmp / "projects/01-crud-api/README.md").write_text("# P\n")
    (tmp / "video/scripts/01-api-foundations").mkdir(parents=True)
    return tmp


class Base(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = make_repo(Path(self._tmp.name))

    def tearDown(self):
        self._tmp.cleanup()

    def write_status(self, data):
        (self.root / "video/status.json").write_text(json.dumps(data))


class CollectTests(Base):
    def test_collects_linked_rows_in_order_and_skips_planned_plain_text(self):
        topics = g.collect_topics(self.root)
        self.assertEqual(
            [t.title for t in topics],
            ["How the Internet Works", "DNS", "CRUD API"],
        )
        dns = topics[1]
        self.assertEqual(dns.part_slug, "01-api-foundations")
        self.assertEqual(dns.part_title, "Part 1 — API Foundations")
        self.assertEqual(dns.number, 2)
        self.assertEqual(dns.path, "docs/01-api-foundations/dns.md")
        self.assertEqual(dns.script, "video/scripts/01-api-foundations/dns.md")

    def test_capstone_path_resolves_to_project_readme_and_script_uses_project_slug(self):
        crud = g.collect_topics(self.root)[-1]
        self.assertEqual(crud.path, "projects/01-crud-api/README.md")
        self.assertEqual(crud.script, "video/scripts/20-capstone-projects/01-crud-api.md")


class StatusTests(Base):
    def topic(self):
        return g.collect_topics(self.root)[1]  # DNS

    def test_planned_when_no_script_and_no_record(self):
        self.assertEqual(g.derive_status(self.topic(), {}, self.root), "planned")

    def test_scripted_when_script_file_exists(self):
        (self.root / "video/scripts/01-api-foundations/dns.md").write_text("x")
        self.assertEqual(g.derive_status(self.topic(), {}, self.root), "scripted")

    def test_rendered_and_published_from_record(self):
        (self.root / "video/scripts/01-api-foundations/dns.md").write_text("x")
        t = self.topic()
        rec = {"docs/01-api-foundations/dns.md": {"status": "rendered"}}
        self.assertEqual(g.derive_status(t, rec, self.root), "rendered")
        rec = {"docs/01-api-foundations/dns.md": {"status": "published", "youtube": "https://youtu.be/abc"}}
        self.assertEqual(g.derive_status(t, rec, self.root), "published")

    def test_validate_rejects_unknown_chapter(self):
        self.write_status({"videos": {"docs/nope.md": {"status": "rendered"}}})
        errors = g.validate_status(g.load_status(self.root), g.collect_topics(self.root), self.root)
        self.assertTrue(any("docs/nope.md" in e for e in errors), errors)

    def test_validate_published_requires_https_youtube_link(self):
        (self.root / "video/scripts/01-api-foundations/dns.md").write_text("x")
        for bad in (None, "", "http://youtu.be/abc", "not a url"):
            rec = {"status": "published"} if bad is None else {"status": "published", "youtube": bad}
            self.write_status({"videos": {"docs/01-api-foundations/dns.md": rec}})
            errors = g.validate_status(g.load_status(self.root), g.collect_topics(self.root), self.root)
            self.assertTrue(any("youtube" in e for e in errors), (bad, errors))

    def test_validate_rendered_requires_script(self):
        self.write_status({"videos": {"docs/01-api-foundations/dns.md": {"status": "rendered"}}})
        errors = g.validate_status(g.load_status(self.root), g.collect_topics(self.root), self.root)
        self.assertTrue(any("script" in e for e in errors), errors)

    def test_validate_rejects_unknown_status_value(self):
        self.write_status({"videos": {"docs/01-api-foundations/dns.md": {"status": "done"}}})
        errors = g.validate_status(g.load_status(self.root), g.collect_topics(self.root), self.root)
        self.assertTrue(any("done" in e for e in errors), errors)

    def test_missing_status_file_means_empty(self):
        self.assertEqual(g.load_status(self.root), {"videos": {}, "pilots": []})


class RenderTests(Base):
    def setUp(self):
        super().setUp()
        (self.root / "video/scripts/01-api-foundations/dns.md").write_text("x")
        self.write_status(
            {
                "pilots": ["docs/01-api-foundations/dns.md"],
                "videos": {
                    "docs/01-api-foundations/dns.md": {"status": "published", "youtube": "https://youtu.be/abc"}
                },
            }
        )

    def text(self):
        return g.render_roadmap(self.root)

    def test_overall_and_per_part_progress_counts(self):
        text = self.text()
        self.assertIn("**1 of 3** topics published", text)
        self.assertIn("| Part 1 — API Foundations | 1 | 0 | 0 | 1 | 2 |", text)

    def test_row_links_chapter_and_youtube(self):
        text = self.text()
        self.assertIn("[DNS](../docs/01-api-foundations/dns.md)", text)
        self.assertIn("[Watch](https://youtu.be/abc)", text)
        self.assertIn("⭐", text)

    def test_next_up_is_first_topic_without_a_script(self):
        self.assertIn("Next up:", self.text())
        self.assertIn("**How the Internet Works**", self.text().split("Next up:")[1].splitlines()[0])

    def test_next_up_prefers_an_unfinished_pilot(self):
        self.write_status(
            {
                "pilots": ["projects/01-crud-api/README.md"],
                "videos": {},
            }
        )
        line = self.text().split("Next up:")[1].splitlines()[0]
        self.assertIn("**CRUD API**", line)
        self.assertIn("pilot", line)

    def test_next_up_skips_pilots_that_already_have_a_script(self):
        (self.root / "video/scripts/20-capstone-projects").mkdir(parents=True)
        (self.root / "video/scripts/20-capstone-projects/01-crud-api.md").write_text("x")
        self.write_status({"pilots": ["projects/01-crud-api/README.md"], "videos": {}})
        line = self.text().split("Next up:")[1].splitlines()[0]
        self.assertIn("**How the Internet Works**", line)

    def test_output_is_deterministic(self):
        self.assertEqual(self.text(), self.text())


class CheckTests(Base):
    def test_check_fails_when_roadmap_is_stale_and_passes_after_write(self):
        self.write_status({"videos": {}})
        self.assertEqual(g.run(self.root, check=True), 1)
        self.assertEqual(g.run(self.root, check=False), 0)
        self.assertTrue((self.root / "video/ROADMAP.md").is_file())
        self.assertEqual(g.run(self.root, check=True), 0)

    def test_run_fails_on_invalid_status_without_writing(self):
        self.write_status({"videos": {"docs/nope.md": {"status": "rendered"}}})
        self.assertEqual(g.run(self.root, check=False), 1)
        self.assertFalse((self.root / "video/ROADMAP.md").exists())


class RealRepoTests(unittest.TestCase):
    def test_every_real_topic_exists_and_is_unique(self):
        topics = g.collect_topics(REPO)
        self.assertGreaterEqual(len(topics), 190)
        paths = [t.path for t in topics]
        self.assertEqual(len(paths), len(set(paths)))
        for t in topics:
            self.assertTrue((REPO / t.path).is_file(), t.path)

    def test_real_status_file_is_valid(self):
        topics = g.collect_topics(REPO)
        self.assertEqual(g.validate_status(g.load_status(REPO), topics, REPO), [])


if __name__ == "__main__":
    unittest.main()

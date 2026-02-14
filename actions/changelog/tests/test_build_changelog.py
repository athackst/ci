from pathlib import Path
import sys
import tempfile
import unittest

ACTION_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ACTION_DIR))

import build_changelog as builder  # noqa: E402
import changelog_config as cfg  # noqa: E402


class ChangelogTests(unittest.TestCase):
    def test_load_changelog_config(self):
        text = """\
template: |
  # What’s Changed

  $CHANGES
categories:
  - title: ':bug: Bug Fixes'
    label: 'bug'
exclude-labels:
  - 'skip-changelog'
"""
        with tempfile.NamedTemporaryFile("w", delete=False) as fh:
            fh.write(text)
            path = fh.name

        parsed = cfg.load_changelog_config(path)
        self.assertEqual(parsed["template"].splitlines()[0], "# What’s Changed")
        self.assertEqual(parsed["categories"][0]["labels"], ["bug"])
        self.assertEqual(parsed["exclude_labels"], {"skip-changelog"})

    def test_category_precedence_exclude_misc(self):
        config = {
            "template": "# What’s Changed\n\n$CHANGES",
            "categories": [
                {"title": ":bug: Bug Fixes", "labels": ["bug", "feature"]},
                {"title": ":rocket: New", "labels": ["feature"]},
            ],
            "exclude_labels": {"skip-changelog"},
        }
        prs = [
            {"number": 1, "title": "Both", "html_url": "https://example/1", "labels": ["bug", "feature"]},
            {"number": 2, "title": "Feature", "html_url": "https://example/2", "labels": ["feature"]},
            {"number": 3, "title": "Skipped", "html_url": "https://example/3", "labels": ["skip-changelog"]},
            {"number": 4, "title": "Other", "html_url": "https://example/4", "labels": ["maintenance"]},
        ]

        out = builder.build_changelog(prs, config)
        self.assertEqual(out["changes"].count("[#1]"), 1)
        self.assertIn("[#2]", out["changes"])
        self.assertNotIn("[#3]", out["changes"])
        self.assertIn("### Miscellaneous", out["changes"])
        self.assertIn("[#4]", out["changes"])
        self.assertEqual(out["pull_requests"], "1,2,4")

    def test_load_prs_from_pr_info_payload(self):
        import json

        payload = {
            "pr_info": {
                "pull_requests": [
                    {"number": 1, "title": "A", "labels": ["bug"]},
                    {"number": 2, "title": "B", "labels": ["feature"]},
                ]
            }
        }
        with tempfile.NamedTemporaryFile("w", delete=False) as fh:
            json.dump(payload, fh)
            path = fh.name

        prs = builder.load_prs(path)
        self.assertEqual(len(prs), 2)


if __name__ == "__main__":
    unittest.main()

import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ACTION_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ACTION_DIR))

import setup_labels as setup_labels_module  # noqa: E402


class SetupLabelsTests(unittest.TestCase):
    def write_file(self, contents: str) -> str:
        with tempfile.NamedTemporaryFile("w", delete=False) as fh:
            fh.write(contents)
            return fh.name

    def test_parse_target_labels_uses_default_color_and_collects_errors(self):
        config_path = self.write_file(
            """\
docs:
  - description: "Docs label"
color-only:
  - color: "1d4ed8"
invalid-color:
  - color: "xyz"
invalid-description:
  - description: 123
empty:
  - changed-files:
      - any-glob-to-any-file: "**/*.md"
"""
        )

        parsed, skipped, errors = setup_labels_module.build_label_plan(config_path)

        self.assertEqual(parsed["docs"]["description"], "Docs label")
        self.assertEqual(parsed["docs"]["color"], setup_labels_module.DEFAULT_COLOR)
        self.assertNotIn("color-only", parsed)
        self.assertEqual(skipped, ["color-only", "empty"])
        self.assertIn("invalid-color: color must be a six-character hex value", errors)
        self.assertIn("invalid-description: description must be a string", errors)

    def test_apply_labels_updates_existing_label(self):
        desired = {
            "docs": {
                "name": "docs",
                "description": "Updated description",
                "color": setup_labels_module.DEFAULT_COLOR,
            }
        }
        existing = {"docs": {"name": "docs", "color": "1d4ed8", "description": "Old"}}

        with mock.patch.object(
            setup_labels_module, "iter_repo_labels", return_value=existing
        ), mock.patch.object(
            setup_labels_module, "api", return_value=({}, {})
        ) as api_mock:
            created, updated, unchanged, errors = setup_labels_module.apply_labels(
                "owner/repo", "token", desired
            )

        self.assertEqual(created, [])
        self.assertEqual(updated, ["docs"])
        self.assertEqual(unchanged, [])
        self.assertEqual(errors, [])
        api_mock.assert_called_once_with(
            "PATCH",
            "https://api.github.com/repos/owner/repo/labels/docs",
            "token",
            payload={
                "new_name": "docs",
                "description": "Updated description",
                "color": setup_labels_module.DEFAULT_COLOR,
            },
        )

    def test_apply_labels_creates_with_default_color_when_missing(self):
        desired = {
            "docs": {
                "name": "docs",
                "description": "Docs label",
                "color": setup_labels_module.DEFAULT_COLOR,
            },
            "bug": {"name": "bug", "color": "1d4ed8", "description": "Bug label"},
        }

        with mock.patch.object(
            setup_labels_module, "iter_repo_labels", return_value={}
        ), mock.patch.object(
            setup_labels_module, "api", return_value=({}, {})
        ) as api_mock:
            created, updated, unchanged, errors = setup_labels_module.apply_labels(
                "owner/repo", "token", desired
            )

        self.assertEqual(created, ["bug", "docs"])
        self.assertEqual(updated, [])
        self.assertEqual(unchanged, [])
        self.assertEqual(errors, [])
        self.assertEqual(api_mock.call_count, 2)

    def test_main_writes_result_payload(self):
        with tempfile.NamedTemporaryFile("r", delete=False) as fh:
            output_path = fh.name

        with mock.patch.object(
            setup_labels_module, "parse_args", return_value=mock.Mock(
                config_path="config.yml",
                repo="owner/repo",
                github_token="token",
                output_path=output_path,
            )
        ), mock.patch.object(
            setup_labels_module,
            "build_label_plan",
            return_value=({"docs": {"name": "docs"}}, ["skip-me"], []),
        ), mock.patch.object(
            setup_labels_module,
            "apply_labels",
            return_value=([], ["docs"], [], ["synthetic failure"]),
        ):
            setup_labels_module.main()

        with open(output_path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        self.assertEqual(payload["updated_labels"], ["docs"])
        self.assertEqual(payload["errors"], ["synthetic failure"])
        self.assertEqual(payload["skipped_labels"], ["skip-me"])


if __name__ == "__main__":
    unittest.main()

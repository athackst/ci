from pathlib import Path
import sys
import tempfile
import unittest

ACTION_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ACTION_DIR))

import build_changelog as changelog  # noqa: E402
import release_drafter_config as config_parser  # noqa: E402
import resolve_next_version as resolver  # noqa: E402


class ReleaseDraftResolverTests(unittest.TestCase):
    def test_parse_version_valid(self):
        self.assertEqual(resolver.parse_version("v1.2.3"), (1, 2, 3))
        self.assertEqual(resolver.parse_version("1.2.3"), (1, 2, 3))

    def test_parse_version_invalid_defaults_to_zero(self):
        self.assertEqual(resolver.parse_version("main"), (0, 0, 0))
        self.assertEqual(resolver.parse_version(""), (0, 0, 0))

    def test_bump_version(self):
        self.assertEqual(resolver.bump_version((1, 2, 3), "major"), (2, 0, 0))
        self.assertEqual(resolver.bump_version((1, 2, 3), "minor"), (1, 3, 0))
        self.assertEqual(resolver.bump_version((1, 2, 3), "patch"), (1, 2, 4))

    def test_select_bump_precedence(self):
        rules = {"major": {"breaking", "major"}, "minor": {"enhancement"}, "patch": set()}
        self.assertEqual(resolver.select_bump({"breaking"}, rules), "major")
        self.assertEqual(resolver.select_bump({"major"}, rules), "major")
        self.assertEqual(resolver.select_bump({"enhancement"}, rules), "minor")
        self.assertEqual(resolver.select_bump({"bug"}, rules), "patch")
        self.assertEqual(resolver.select_bump(set(), rules), "patch")

    def test_load_release_drafter_config(self):
        config_text = """\
categories:
  - title: 'Feature'
    labels:
      - 'enhancement'
      - 'feature'
  - title: 'Bug'
    label: 'bug'
version-resolver:
  major:
    labels:
      - 'breaking'
      - 'major'
  minor:
    labels:
      - 'enhancement'
  patch:
    labels:
      - 'bug'
      - 'documentation'
exclude-labels:
  - 'skip-changelog'
"""
        with tempfile.NamedTemporaryFile("w", delete=False) as fh:
            fh.write(config_text)
            config_path = fh.name

        config = config_parser.load_release_drafter_config(config_path)
        rules = config["version_resolver"]
        excluded = config["exclude_labels"]
        self.assertEqual(rules["major"], {"breaking", "major"})
        self.assertEqual(rules["minor"], {"enhancement"})
        self.assertEqual(rules["patch"], {"bug", "documentation"})
        self.assertEqual(excluded, {"skip-changelog"})
        self.assertEqual(
            config["categories"],
            [
                {"title": "Feature", "labels": ["enhancement", "feature"]},
                {"title": "Bug", "labels": ["bug"]},
            ],
        )

    def test_build_changes_respects_exclude_and_categories(self):
        config = {
            "exclude_labels": {"skip-changelog"},
            "categories": [
                {"title": "Bug Fixes", "labels": ["bug"]},
                {"title": "New", "labels": ["enhancement"]},
            ],
        }
        prs = [
            {
                "number": 1,
                "title": "Fix A",
                "html_url": "https://example/pr/1",
                "user": {"login": "alice"},
                "labels": [{"name": "bug"}],
            },
            {
                "number": 2,
                "title": "Skip B",
                "html_url": "https://example/pr/2",
                "user": {"login": "bob"},
                "labels": [{"name": "skip-changelog"}, {"name": "enhancement"}],
            },
            {
                "number": 3,
                "title": "Other C",
                "html_url": "https://example/pr/3",
                "user": {"login": "cora"},
                "labels": [{"name": "maintenance"}],
            },
        ]
        changes, pr_ids = changelog.build_changes(prs, config)
        self.assertIn("Bug Fixes", changes)
        self.assertIn("#1", changes)
        self.assertIn("Other Changes", changes)
        self.assertIn("#3", changes)
        self.assertNotIn("#2", changes)
        self.assertEqual(pr_ids, ["1", "3"])

    def test_resolve_base_ref_prefers_latest_tag(self):
        from_ref, used_tag = resolver.resolve_base_ref(["v2.0.0", "v1.0.0"], "abc123")
        self.assertEqual(from_ref, "v2.0.0")
        self.assertTrue(used_tag)

    def test_is_semver_tag(self):
        self.assertTrue(resolver.is_semver_tag("v1.2.3"))
        self.assertFalse(resolver.is_semver_tag("1.2.3"))
        self.assertFalse(resolver.is_semver_tag("ci-test-123"))

    def test_get_latest_semver_tag(self):
        tags = ["ci-test-123", "v2.0.0", "v1.9.0"]
        self.assertEqual(resolver.get_latest_semver_tag(tags), "v2.0.0")
        self.assertIsNone(resolver.get_latest_semver_tag(["ci-test-123", "dev-tag"]))

    def test_resolve_base_ref_falls_back_to_first_commit(self):
        from_ref, used_tag = resolver.resolve_base_ref([], "abc123")
        self.assertEqual(from_ref, "abc123")
        self.assertFalse(used_tag)

    def test_build_release_names(self):
        tag_name, release_name = resolver.build_release(
            "1.2.3",
            "Release v$RESOLVED_VERSION",
            "v$RESOLVED_VERSION",
        )
        self.assertEqual(tag_name, "v1.2.3")
        self.assertEqual(release_name, "Release v1.2.3")

    def test_build_release_names_from_custom_templates(self):
        tag_name, release_name = resolver.build_release(
            "1.2.3",
            "Draft $RESOLVED_VERSION",
            "release-$RESOLVED_VERSION",
        )
        self.assertEqual(tag_name, "release-1.2.3")
        self.assertEqual(release_name, "Draft 1.2.3")


if __name__ == "__main__":
    unittest.main()

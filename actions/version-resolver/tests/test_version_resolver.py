from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest import mock

ACTION_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ACTION_DIR))

import version_config as config_parser  # noqa: E402
import version_resolver as resolver  # noqa: E402


class VersionResolverTests(unittest.TestCase):
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
        rules = {"major": {"breaking", "major"}, "minor": {"feature"}, "patch": set()}
        self.assertEqual(resolver.select_bump({"breaking"}, rules), "major")
        self.assertEqual(resolver.select_bump({"feature"}, rules), "minor")
        self.assertEqual(resolver.select_bump({"bug"}, rules), "patch")

    def test_is_semver_tag(self):
        self.assertTrue(resolver.is_semver_tag("v1.2.3"))
        self.assertTrue(resolver.is_semver_tag("1.2.3"))
        self.assertFalse(resolver.is_semver_tag("ci-test-123"))

    def test_get_latest_semver_tag(self):
        tags = ["ci-test-123", "2.0.0", "v1.9.0"]
        self.assertEqual(resolver.get_latest_semver_tag(tags), "2.0.0")
        self.assertIsNone(resolver.get_latest_semver_tag(["ci-test-123", "dev-tag"]))

    def test_resolve_base_ref(self):
        self.assertEqual(resolver.resolve_base_ref(["v2.0.0"], "abc123"), "v2.0.0")
        self.assertEqual(resolver.resolve_base_ref([], "abc123"), "abc123")

    def test_load_version_config(self):
        config_text = """\
version-resolver:
  major:
    labels:
      - 'breaking'
  minor:
    labels:
      - 'feature'
  patch:
    labels:
      - 'bug'
"""
        with tempfile.NamedTemporaryFile("w", delete=False) as fh:
            fh.write(config_text)
            config_path = fh.name

        config = config_parser.load_version_config(config_path)
        self.assertEqual(config["version_resolver"]["major"], {"breaking"})

    def test_pr_labels(self):
        pr = {"labels": [{"name": "bug"}, {"name": None}, {"name": "docs"}]}
        self.assertEqual(resolver.pr_labels(pr), {"bug", "docs"})

    def test_compact_pr(self):
        pr = {
            "number": 12,
            "title": "Add feature",
            "html_url": "https://example/pr/12",
            "merged_at": "2024-01-01T00:00:00Z",
            "merge_commit_sha": "abc123",
            "labels": [{"name": "feature"}, {"name": "docs"}],
        }
        compact = resolver.compact_pr(pr)
        self.assertEqual(compact["number"], 12)
        self.assertEqual(compact["title"], "Add feature")
        self.assertEqual(compact["labels"], ["docs", "feature"])

    def test_fetch_merged_prs_from_graphql_search_filters_and_deduplicates(self):
        graphql_page = {
            "search": {
                "pageInfo": {"hasNextPage": False, "endCursor": None},
                "nodes": [
                    {
                        "number": 1,
                        "title": "Feature",
                        "url": "https://example/pr/1",
                        "mergedAt": "2024-01-01T00:00:00Z",
                        "mergeCommit": {"oid": "sha1"},
                        "labels": {"nodes": [{"name": "feature"}]},
                    },
                    {
                        "number": 1,
                        "title": "Feature duplicate",
                        "url": "https://example/pr/1",
                        "mergedAt": "2024-01-01T00:00:00Z",
                        "mergeCommit": {"oid": "sha1"},
                        "labels": {"nodes": [{"name": "feature"}]},
                    },
                    {
                        "number": 2,
                        "title": "Out of range",
                        "url": "https://example/pr/2",
                        "mergedAt": "2024-01-02T00:00:00Z",
                        "mergeCommit": {"oid": "sha-out"},
                        "labels": {"nodes": [{"name": "bug"}]},
                    },
                ],
            }
        }
        with mock.patch.object(
            resolver,
            "gh_graphql",
            return_value=graphql_page,
        ), mock.patch.object(
            resolver,
            "get_ref_commit_date",
            side_effect=["2024-01-01T00:00:00Z", "2024-01-10T00:00:00Z"],
        ):
            prs = resolver.fetch_merged_prs_from_graphql_search(
                "owner/repo",
                "token",
                "from",
                "to",
                {"sha1"},
            )
        self.assertEqual(sorted(pr["number"] for pr in prs), [1])

    def test_fetch_merged_prs_falls_back_to_pagination(self):
        with mock.patch.object(
            resolver,
            "fetch_merged_prs_from_graphql_search",
            side_effect=RuntimeError("graphql failed"),
        ), mock.patch.object(
            resolver,
            "fetch_merged_prs_from_pagination",
            return_value=[{"number": 9, "labels": [{"name": "feature"}], "merged_at": "2024-01-01"}],
        ) as fallback:
            prs = resolver.fetch_merged_prs("owner/repo", "token", "from", "to", {"sha"})
        fallback.assert_called_once()
        self.assertEqual([pr["number"] for pr in prs], [9])

    def test_get_current_pr_from_event(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as fh:
            json.dump(
                {
                    "pull_request": {
                        "number": 42,
                        "title": "My PR",
                        "html_url": "https://example/pr/42",
                        "merged_at": None,
                        "merge_commit_sha": None,
                        "labels": [{"name": "feature"}],
                        "base": {"repo": {"full_name": "owner/repo"}},
                    }
                },
                fh,
            )
            event_path = fh.name

        with mock.patch.dict(
            "os.environ",
            {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_EVENT_PATH": event_path},
            clear=False,
        ):
            pr = resolver.get_current_pr_from_event("owner/repo")

        self.assertIsNotNone(pr)
        self.assertEqual(pr["number"], 42)
        self.assertEqual(pr["labels"], [{"name": "feature"}])

    def test_resolve_all(self):
        config_text = """\
version-resolver:
  major:
    labels:
      - 'breaking'
  minor:
    labels:
      - 'feature'
  patch:
    labels:
      - 'bug'
"""
        with tempfile.NamedTemporaryFile("w", delete=False) as fh:
            fh.write(config_text)
            config_path = fh.name

        prs = [
            {"labels": [{"name": "bug"}]},
            {"labels": [{"name": "feature"}]},
        ]
        with mock.patch.object(resolver, "get_tags", return_value=["v1.2.3"]), mock.patch.object(
            resolver, "get_first_commit", return_value="abc123"
        ), mock.patch.object(resolver, "get_commit_range", return_value={"sha1"}), mock.patch.object(
            resolver, "fetch_merged_prs", return_value=prs
        ):
            out = resolver.resolve_all(config_path, "owner/repo", "token", "HEAD")

        self.assertEqual(out["from_ref"], "v1.2.3")
        self.assertEqual(out["latest_semver_tag"], "v1.2.3")
        self.assertEqual(out["to_ref"], "HEAD")
        self.assertEqual(out["pr_info"]["labels"], ["bug", "feature"])
        self.assertEqual(len(out["pr_info"]["pull_requests"]), 2)
        self.assertEqual(out["resolved_version"], "1.3.0")
        self.assertEqual(out["major_version"], "1")
        self.assertEqual(out["minor_version"], "3")
        self.assertEqual(out["patch_version"], "0")

    def test_to_line(self):
        out = resolver.to_line(
            {
                "from_ref": "v1.2.3",
                "latest_semver_tag": "v1.2.3",
                "resolved_version": "1.3.0",
                "major_version": "1",
                "minor_version": "3",
                "patch_version": "0",
            }
        )
        self.assertIn("from-ref=v1.2.3", out)
        self.assertIn("latest-semver-tag=v1.2.3", out)
        self.assertIn("resolved-version=1.3.0", out)
        self.assertIn("major-version=1", out)
        self.assertIn("minor-version=3", out)
        self.assertIn("patch-version=0", out)

    def test_write_data_file(self):
        payload = {"from_ref": "v1.2.3", "resolved_version": "1.3.0"}
        with tempfile.NamedTemporaryFile("r", delete=False) as fh:
            output_path = fh.name

        resolver.write_data_file(payload, output_path)
        with open(output_path, "r", encoding="utf-8") as fh:
            loaded = json.load(fh)
        self.assertEqual(loaded, payload)


if __name__ == "__main__":
    unittest.main()

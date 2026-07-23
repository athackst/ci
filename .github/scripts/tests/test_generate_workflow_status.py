import json
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import generate_workflow_status  # noqa: E402


class FakeClient:
    def __init__(self, rest_responses=None, graphql_responses=None):
        self.rest_responses = rest_responses or {}
        self.graphql_responses = list(graphql_responses or [])
        self.graphql_queries = []

    def get_json(self, path, *, params=None):
        key = (path, tuple(sorted((params or {}).items())))
        return self.rest_responses[key]

    def graphql(self, query):
        self.graphql_queries.append(query)
        return self.graphql_responses.pop(0)


class GenerateWorkflowStatusTests(unittest.TestCase):
    def test_resolve_owners_deduplicates_cli_values(self):
        self.assertEqual(
            generate_workflow_status.resolve_owners(
                ["athackst", "PrimerPages", "athackst"],
            ),
            ["athackst", "PrimerPages"],
        )

    def test_resolve_owners_rejects_invalid_or_empty_values(self):
        with self.assertRaisesRegex(ValueError, "Invalid repository owner"):
            generate_workflow_status.resolve_owners(["owner/name"])
        with self.assertRaisesRegex(ValueError, "No repository owners configured"):
            generate_workflow_status.resolve_owners([])

    def test_discover_repositories_handles_users_orgs_pagination_and_filters(self):
        first_page = [
            {
                "name": f"repo-{index}",
                "owner": {"login": "athackst"},
                "private": False,
                "fork": False,
                "archived": False,
            }
            for index in range(100)
        ]
        client = FakeClient(
            rest_responses={
                ("/users/athackst", ()): {"type": "User"},
                (
                    "/users/athackst/repos",
                    (("page", 1), ("per_page", 100)),
                ): first_page,
                (
                    "/users/athackst/repos",
                    (("page", 2), ("per_page", 100)),
                ): [
                    {
                        "name": "fork",
                        "owner": {"login": "athackst"},
                        "private": False,
                        "fork": True,
                        "archived": False,
                    },
                    {
                        "name": "final",
                        "owner": {"login": "athackst"},
                        "private": False,
                        "fork": False,
                        "archived": False,
                    },
                ],
                ("/users/PrimerPages", ()): {"type": "Organization"},
                (
                    "/orgs/PrimerPages/repos",
                    (("page", 1), ("per_page", 100)),
                ): [
                    {
                        "name": "site",
                        "owner": {"login": "PrimerPages"},
                        "private": False,
                        "fork": False,
                        "archived": False,
                    },
                    {
                        "name": "archived",
                        "owner": {"login": "PrimerPages"},
                        "private": False,
                        "fork": False,
                        "archived": True,
                    },
                ],
            }
        )

        repositories = generate_workflow_status.discover_repositories(
            ["athackst", "PrimerPages"],
            client,
        )

        self.assertEqual(len(repositories), 102)
        self.assertIn(
            generate_workflow_status.Repository("athackst", "final"),
            repositories,
        )
        self.assertIn(
            generate_workflow_status.Repository("PrimerPages", "site"),
            repositories,
        )
        self.assertNotIn(
            generate_workflow_status.Repository("athackst", "fork"),
            repositories,
        )

    def test_inspect_managed_repositories_filters_answers_and_maps_workflows(self):
        repositories = [
            generate_workflow_status.Repository("athackst", "first"),
            generate_workflow_status.Repository("athackst", "unmanaged"),
            generate_workflow_status.Repository("PrimerPages", "second"),
        ]
        client = FakeClient(
            graphql_responses=[
                {
                    "repo_0": {
                        "answers": {"__typename": "Blob"},
                        "workflows": {
                            "__typename": "Tree",
                            "entries": [
                                {"name": "ci_update.yml", "type": "blob"},
                                {"name": "nested", "type": "tree"},
                            ],
                        },
                    },
                    "repo_1": {
                        "answers": None,
                        "workflows": None,
                    },
                },
                {
                    "repo_0": {
                        "answers": {"__typename": "Blob"},
                        "workflows": {
                            "__typename": "Tree",
                            "entries": [{"name": "site.yml", "type": "blob"}],
                        },
                    }
                },
            ]
        )

        managed, workflows = (
            generate_workflow_status.inspect_managed_repositories(
                repositories,
                client,
                answers_file=".copier-answers.ci.yml",
                chunk_size=2,
            )
        )

        self.assertEqual(
            [repository.full_name for repository in managed],
            ["athackst/first", "PrimerPages/second"],
        )
        self.assertEqual(workflows["athackst/first"], {"ci_update.yml"})
        self.assertEqual(workflows["PrimerPages/second"], {"site.yml"})
        self.assertEqual(len(client.graphql_queries), 2)
        self.assertIn("HEAD:.copier-answers.ci.yml", client.graphql_queries[0])

    def test_retry_delay_uses_headers_and_rate_limit_message(self):
        self.assertEqual(
            generate_workflow_status.retry_delay_seconds(
                {"Retry-After": "7"},
                "",
            ),
            7,
        )
        self.assertEqual(
            generate_workflow_status.retry_delay_seconds(
                {},
                "Secondary rate limit exceeded",
            ),
            5,
        )
        self.assertIsNone(
            generate_workflow_status.retry_delay_seconds({}, "Forbidden")
        )

    def test_render_status_shows_badges_and_missing_workflows(self):
        repositories = [
            generate_workflow_status.Repository("athackst", "example")
        ]
        output = generate_workflow_status.render_status(
            repositories,
            {"athackst/example": {"ci_update.yml"}},
            [
                ".github/workflows/ci_update.yml",
                ".github/workflows/site.yml",
            ],
        )

        self.assertIn("- Repositories shown: 1", output)
        self.assertIn("- Managed workflows shown: 2", output)
        self.assertIn("| Repository | ci_update | site |", output)
        self.assertIn(
            "https://github.com/athackst/example/actions/workflows/"
            "ci_update.yml/badge.svg",
            output,
        )
        self.assertIn(" | - |", output)

    def test_main_generates_output_without_intermediate_repository_file(self):
        repository = generate_workflow_status.Repository("athackst", "example")
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            managed_paths = temp_path / "copier_update_paths.txt"
            output_path = temp_path / "workflow_status.md"
            managed_paths.write_text(".github/workflows/ci_update.yml\n")
            args = SimpleNamespace(
                owner=["athackst"],
                answers_file=".copier-answers.ci.yml",
                managed_paths_file=managed_paths,
                output_path=output_path,
                chunk_size=30,
            )

            with (
                patch.object(generate_workflow_status, "parse_args", return_value=args),
                patch.object(
                    generate_workflow_status,
                    "discover_repositories",
                    return_value=[repository],
                ),
                patch.object(
                    generate_workflow_status,
                    "inspect_managed_repositories",
                    return_value=([repository], {"athackst/example": {"ci_update.yml"}}),
                ),
                patch.dict("os.environ", {"GITHUB_TOKEN": "token"}, clear=True),
            ):
                status = generate_workflow_status.main()

            output = output_path.read_text()

        self.assertEqual(status, 0)
        self.assertIn("athackst/example", output)
        self.assertIn("ci_update.yml/badge.svg", output)


if __name__ == "__main__":
    unittest.main()

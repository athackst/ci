import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS_DIR))

import generate_workflow_status  # noqa: E402


class GenerateWorkflowStatusTests(unittest.TestCase):
    def test_load_matching_repositories_filters_and_sorts(self):
        records = [
            {"full_name": "zeta/public"},
            {"full_name": "alpha/private", "private": True},
            {"full_name": "alpha/fork", "fork": True},
            {"full_name": "alpha/archived", "archived": True},
            "Alpha/Public",
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            repos_file = Path(temp_dir) / "repositories.json"
            repos_file.write_text(json.dumps(records))

            repositories = generate_workflow_status.load_matching_repositories(repos_file)

        self.assertEqual(
            [repository["full_name"] for repository in repositories],
            ["Alpha/Public", "zeta/public"],
        )

    def test_retry_delay_uses_headers_and_rate_limit_message(self):
        self.assertEqual(
            generate_workflow_status._retry_delay_seconds({"Retry-After": "7"}, ""),
            7,
        )
        self.assertEqual(
            generate_workflow_status._retry_delay_seconds({}, "Secondary rate limit exceeded"),
            5,
        )
        self.assertIsNone(generate_workflow_status._retry_delay_seconds({}, "Forbidden"))

    def test_list_remote_workflow_files_batched_maps_blob_entries(self):
        repositories = [
            {
                "owner": "athackst",
                "name": "first",
                "full_name": "athackst/first",
            },
            {
                "owner": "PrimerPages",
                "name": "second",
                "full_name": "PrimerPages/second",
            },
        ]
        responses = [
            {
                "repo_0": {
                    "workflows": {
                        "__typename": "Tree",
                        "entries": [
                            {"name": "ci_update.yml", "type": "blob"},
                            {"name": "nested", "type": "tree"},
                        ],
                    }
                }
            },
            {
                "repo_0": {
                    "workflows": {
                        "__typename": "Tree",
                        "entries": [{"name": "site.yml", "type": "blob"}],
                    }
                }
            },
        ]

        with patch.object(
            generate_workflow_status,
            "graphql_request",
            side_effect=responses,
        ) as request:
            workflows = generate_workflow_status.list_remote_workflow_files_batched(
                repositories,
                "token",
                chunk_size=1,
            )

        self.assertEqual(request.call_count, 2)
        self.assertEqual(workflows["athackst/first"], {"ci_update.yml"})
        self.assertEqual(workflows["PrimerPages/second"], {"site.yml"})

    def test_main_renders_badges_only_for_workflows_present_in_repository(self):
        repositories = [
            {
                "owner": "athackst",
                "name": "example",
                "full_name": "athackst/example",
                "private": False,
                "fork": False,
                "archived": False,
            }
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            repos_file = temp_path / "repositories.json"
            copier_paths = temp_path / "copier_update_paths.txt"
            output_path = temp_path / "workflow_status.md"
            repos_file.write_text(json.dumps(repositories))
            copier_paths.write_text(
                ".github/workflows/ci_update.yml\n"
                ".github/workflows/site.yml\n"
                "README.md\n"
            )

            with (
                patch.object(generate_workflow_status, "COPIER_PATHS", copier_paths),
                patch.object(
                    generate_workflow_status,
                    "list_remote_workflow_files_batched",
                    return_value={"athackst/example": {"ci_update.yml"}},
                ),
                patch.object(
                    sys,
                    "argv",
                    [
                        "generate_workflow_status.py",
                        "--repos-file",
                        str(repos_file),
                        "--output-path",
                        str(output_path),
                    ],
                ),
            ):
                generate_workflow_status.main()

            output = output_path.read_text()

        self.assertIn("- Repositories shown: 1", output)
        self.assertIn("- Managed workflows shown: 2", output)
        self.assertIn("| Repository | ci_update | site |", output)
        self.assertIn(
            "https://github.com/athackst/example/actions/workflows/ci_update.yml/badge.svg",
            output,
        )
        self.assertIn("| [`athackst/example`](https://github.com/athackst/example) |", output)
        self.assertIn(" | - |", output)


if __name__ == "__main__":
    unittest.main()

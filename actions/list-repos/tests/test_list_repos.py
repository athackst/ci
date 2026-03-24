from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
from urllib.error import HTTPError

ACTION_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ACTION_DIR))

import list_repos  # noqa: E402


class FakeClient:
    def __init__(self, responses, existing_paths=None):
        self.responses = responses
        self.existing_paths = existing_paths or set()

    def get_json(self, path, *, params=None):
        key = (path, tuple(sorted((params or {}).items())))
        value = self.responses[key]
        if isinstance(value, Exception):
            raise value
        return value

    def path_exists(self, full_name, filter_path):
        return (full_name, filter_path) in self.existing_paths


class ListReposTests(unittest.TestCase):
    def make_args(self, **overrides):
        values = {
            "user": "athackst",
            "public": "true",
            "private": "true",
            "fork": "true",
            "archived": "true",
            "filter_paths": [],
        }
        values.update(overrides)
        return SimpleNamespace(**values)

    def test_collect_repositories_filters_public_non_fork_non_archived(self):
        client = FakeClient(
            {
                ("/users/athackst", ()): {"type": "User"},
                (
                    "/users/athackst/repos",
                    (("page", 1), ("per_page", 100)),
                ): [
                    {"full_name": "athackst/repo-public-1", "private": False, "fork": False, "archived": False},
                    {"full_name": "athackst/repo-fork-1", "private": False, "fork": True, "archived": False},
                    {"full_name": "athackst/repo-archived-1", "private": False, "fork": False, "archived": True},
                ],
            }
        )
        args = self.make_args(public="true", private="false", fork="false", archived="false")

        repositories = list_repos.collect_repositories(args, client)

        self.assertEqual(
            repositories,
            [
                {
                    "owner": "athackst",
                    "name": "repo-public-1",
                    "full_name": "athackst/repo-public-1",
                    "private": False,
                    "fork": False,
                    "archived": False,
                }
            ],
        )

    def test_collect_repositories_filters_private(self):
        client = FakeClient(
            {
                ("/users/athackst", ()): {"type": "User"},
                (
                    "/user/repos",
                    (("affiliation", "owner"), ("page", 1), ("per_page", 100), ("visibility", "all")),
                ): [
                    {"full_name": "athackst/repo-public-2", "private": False, "fork": False, "archived": False},
                    {"full_name": "athackst/repo-private-1", "private": True, "fork": False, "archived": False},
                ],
            }
        )
        args = self.make_args(public="false", private="true", fork="false", archived="false")

        repositories = list_repos.collect_repositories(args, client)

        self.assertEqual([repo["name"] for repo in repositories], ["repo-private-1"])

    def test_collect_repositories_uses_installation_fallback(self):
        client = FakeClient(
            {
                ("/users/athackst", ()): {"type": "User"},
                (
                    "/user/repos",
                    (("affiliation", "owner"), ("page", 1), ("per_page", 100), ("visibility", "all")),
                ): HTTPError(
                    url="https://api.github.com/user/repos",
                    code=403,
                    msg="forbidden",
                    hdrs=None,
                    fp=None,
                ),
                (
                    "/installation/repositories",
                    (("page", 1), ("per_page", 100)),
                ): {
                    "repositories": [
                        {"full_name": "athackst/repo-private-1", "private": True, "fork": False, "archived": False},
                    ]
                },
            }
        )
        args = self.make_args(public="false", private="true", fork="false", archived="false")

        repositories = list_repos.collect_repositories(args, client)

        self.assertEqual([repo["name"] for repo in repositories], ["repo-private-1"])

    def test_collect_repositories_applies_filter_paths(self):
        client = FakeClient(
            {
                ("/users/athackst", ()): {"type": "User"},
                (
                    "/user/repos",
                    (("affiliation", "owner"), ("page", 1), ("per_page", 100), ("visibility", "all")),
                ): [
                    {"full_name": "athackst/repo-public-2", "private": False, "fork": False, "archived": False},
                    {"full_name": "athackst/repo-private-1", "private": True, "fork": False, "archived": False},
                ],
            },
            existing_paths={("athackst/repo-public-2", ".copier-answers.ci.yml")},
        )
        args = self.make_args(fork="false", archived="false", filter_paths=[".copier-answers.ci.yml"])

        repositories = list_repos.collect_repositories(args, client)

        self.assertEqual([repo["name"] for repo in repositories], ["repo-public-2"])

    def test_collect_repositories_returns_empty_when_public_and_private_disabled(self):
        client = FakeClient({("/users/athackst", ()): {"type": "User"}})
        args = self.make_args(public="false", private="false")

        repositories = list_repos.collect_repositories(args, client)

        self.assertEqual(repositories, [])

    def test_collect_repositories_filters_public_organization_repos(self):
        client = FakeClient(
            {
                ("/users/athackst", ()): {"type": "Organization"},
                (
                    "/orgs/athackst/repos",
                    (("page", 1), ("per_page", 100)),
                ): [
                    {"full_name": "athackst/repo-public-1", "private": False, "fork": False, "archived": False},
                    {"full_name": "someone-else/repo-public-2", "private": False, "fork": False, "archived": False},
                    {"full_name": "athackst/repo-archived-1", "private": False, "fork": False, "archived": True},
                ],
            }
        )
        args = self.make_args(public="true", private="false", fork="false", archived="false")

        repositories = list_repos.collect_repositories(args, client)

        self.assertEqual([repo["name"] for repo in repositories], ["repo-public-1"])

    def test_collect_repositories_uses_installation_fallback_for_organization(self):
        client = FakeClient(
            {
                ("/users/athackst", ()): {"type": "Organization"},
                (
                    "/user/repos",
                    (("affiliation", "owner"), ("page", 1), ("per_page", 100), ("visibility", "all")),
                ): HTTPError(
                    url="https://api.github.com/user/repos",
                    code=403,
                    msg="forbidden",
                    hdrs=None,
                    fp=None,
                ),
                (
                    "/installation/repositories",
                    (("page", 1), ("per_page", 100)),
                ): {
                    "repositories": [
                        {"full_name": "athackst/repo-private-1", "private": True, "fork": False, "archived": False},
                        {"full_name": "someone-else/repo-private-2", "private": True, "fork": False, "archived": False},
                    ]
                },
            }
        )
        args = self.make_args(public="false", private="true", fork="false", archived="false")

        repositories = list_repos.collect_repositories(args, client)

        self.assertEqual([repo["name"] for repo in repositories], ["repo-private-1"])

    def test_collect_repositories_rejects_unsupported_owner_type(self):
        client = FakeClient({("/users/athackst", ()): {"type": "Enterprise"}})
        args = self.make_args()

        with self.assertRaisesRegex(ValueError, "Expected GitHub user or organization"):
            list_repos.collect_repositories(args, client)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from urllib.error import HTTPError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

API_BASE = "https://api.github.com"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List repositories for a GitHub user as JSON."
    )
    parser.add_argument("--user", required=True, help="GitHub username to inspect.")
    parser.add_argument(
        "--public",
        choices=["true", "false"],
        default="true",
        help="Include public repositories.",
    )
    parser.add_argument(
        "--private",
        choices=["true", "false"],
        default="true",
        help="Include private repositories.",
    )
    parser.add_argument(
        "--fork",
        choices=["true", "false"],
        default="true",
        help="Include fork repositories.",
    )
    parser.add_argument(
        "--archived",
        choices=["true", "false"],
        default="true",
        help="Include archived repositories.",
    )
    parser.add_argument(
        "--filter-path",
        action="append",
        default=[],
        dest="filter_paths",
        help="Repository path that must exist. May be provided multiple times.",
    )
    parser.add_argument(
        "--debug-timing",
        action="store_true",
        help="Print timing diagnostics to stderr.",
    )
    return parser.parse_args()


def resolve_token() -> str | None:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    try:
        return subprocess.check_output(["gh", "auth", "token"], text=True).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


class GitHubClient:
    def __init__(self, token: str | None) -> None:
        self.token = token

    def get_json(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        query = f"?{urlencode(params)}" if params else ""
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "athackst-ci-list-repos",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        request = Request(f"{API_BASE}{path}{query}", headers=headers)
        with urlopen(request) as response:
            return json.load(response)

    def path_exists(self, full_name: str, filter_path: str) -> bool:
        try:
            self.get_json(
                f"/repos/{quote(full_name, safe='/')}/contents/{quote(filter_path, safe='/')}"
            )
            return True
        except HTTPError as error:
            if error.code == 404:
                return False
            raise


def list_response_items(
    client: GitHubClient, user: str, include_private: bool, page: int
) -> list[dict[str, Any]]:
    if not include_private:
        return list_public_response_items(client, user, page)

    try:
        return client.get_json(
            "/user/repos",
            params={"visibility": "all", "affiliation": "owner", "page": page, "per_page": 100},
        )
    except HTTPError:
        response = client.get_json(
            "/installation/repositories", params={"page": page, "per_page": 100}
        )
        return response["repositories"]


def list_public_response_items(
    client: GitHubClient, user: str, page: int
) -> list[dict[str, Any]]:
    return client.get_json(
        f"/users/{quote(user)}/repos", params={"page": page, "per_page": 100}
    )


def normalize_repository(item: dict[str, Any]) -> dict[str, Any]:
    full_name = item["full_name"]
    owner, name = full_name.split("/", 1)
    owner_data = item.get("owner") or {}
    return {
        "owner": owner_data.get("login", owner),
        "name": item.get("name", name),
        "full_name": full_name,
        "private": bool(item.get("private", False)),
        "fork": bool(item.get("fork", False)),
        "archived": bool(item.get("archived", False)),
    }


def include_repository(
    repository: dict[str, Any],
    *,
    include_public: bool,
    include_private: bool,
    include_forks: bool,
    include_archived: bool,
) -> bool:
    is_private = repository["private"]
    if is_private and not include_private:
        return False
    if not is_private and not include_public:
        return False
    if repository["fork"] and not include_forks:
        return False
    if repository["archived"] and not include_archived:
        return False
    return True


def matches_filter_paths(
    client: GitHubClient, full_name: str, filter_paths: list[str]
) -> bool:
    if not filter_paths:
        return True
    return any(client.path_exists(full_name, filter_path) for filter_path in filter_paths)


def log_timing(args: argparse.Namespace, **metrics: float | int) -> None:
    if not args.debug_timing:
        return

    print("list_repos timing:", file=sys.stderr)
    ordered_keys = [
        "owner_check_seconds",
        "listing_seconds",
        "filter_path_seconds",
        "total_seconds",
        "repository_count",
        "filter_path_count",
    ]
    for key in ordered_keys:
        if key not in metrics:
            continue
        value = metrics[key]
        if isinstance(value, float):
            print(f"  - {key}: {value:.3f}", file=sys.stderr)
        else:
            print(f"  - {key}: {value}", file=sys.stderr)


def timed_collect_repositories(
    args: argparse.Namespace, client: GitHubClient
) -> tuple[list[dict[str, Any]], dict[str, float | int]]:
    include_public = args.public == "true"
    include_private = args.private == "true"
    include_forks = args.fork == "true"
    include_archived = args.archived == "true"

    if not include_public and not include_private:
        return [], {
            "owner_check_seconds": 0.0,
            "listing_seconds": 0.0,
            "filter_path_seconds": 0.0,
            "repository_count": 0,
            "filter_path_count": len(args.filter_paths),
        }

    owner_check_start = time.perf_counter()
    owner_type = client.get_json(f"/users/{quote(args.user)}")["type"]
    owner_check_seconds = time.perf_counter() - owner_check_start
    if owner_type != "User":
        raise ValueError(f"Expected GitHub user, got: {owner_type}")

    listing_start = time.perf_counter()
    page = 1
    repositories: list[dict[str, Any]] = []
    while True:
        if include_private:
            response_items = list_response_items(client, args.user, include_private, page)
        else:
            response_items = list_public_response_items(client, args.user, page)

        page_repositories: list[dict[str, Any]] = []
        for item in response_items:
            repository = normalize_repository(item)
            if repository["owner"] != args.user:
                continue
            if include_repository(
                repository,
                include_public=include_public,
                include_private=include_private,
                include_forks=include_forks,
                include_archived=include_archived,
            ):
                page_repositories.append(repository)

        repositories.extend(page_repositories)

        if len(response_items) < 100:
            break
        page += 1

    listing_seconds = time.perf_counter() - listing_start

    filter_path_seconds = 0.0
    if args.filter_paths:
        filter_start = time.perf_counter()
        max_workers = min(16, max(1, len(repositories)))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            matches = list(
                executor.map(
                    lambda repo: matches_filter_paths(client, repo["full_name"], args.filter_paths),
                    repositories,
                )
            )
        repositories = [
            repository
            for repository, matched in zip(repositories, matches, strict=False)
            if matched
        ]
        filter_path_seconds = time.perf_counter() - filter_start

    return repositories, {
        "owner_check_seconds": owner_check_seconds,
        "listing_seconds": listing_seconds,
        "filter_path_seconds": filter_path_seconds,
        "repository_count": len(repositories),
        "filter_path_count": len(args.filter_paths),
    }


def collect_repositories(args: argparse.Namespace, client: GitHubClient) -> list[dict[str, Any]]:
    repositories, _ = timed_collect_repositories(args, client)
    return repositories


def main() -> int:
    args = parse_args()
    client = GitHubClient(resolve_token())

    try:
        total_start = time.perf_counter()
        repositories, metrics = timed_collect_repositories(args, client)
        total_seconds = time.perf_counter() - total_start
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 1

    log_timing(
        args,
        owner_check_seconds=metrics["owner_check_seconds"],
        listing_seconds=metrics["listing_seconds"],
        filter_path_seconds=metrics["filter_path_seconds"],
        total_seconds=total_seconds,
        repository_count=metrics["repository_count"],
        filter_path_count=metrics["filter_path_count"],
    )
    print(json.dumps(repositories, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

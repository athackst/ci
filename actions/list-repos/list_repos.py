#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Any


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
    return parser.parse_args()


def gh_api(path: str, *, suppress_stderr: bool = False) -> Any:
    stderr = subprocess.DEVNULL if suppress_stderr else None
    output = subprocess.check_output(["gh", "api", path], text=True, stderr=stderr)
    return json.loads(output)


def gh_api_ok(path: str) -> bool:
    result = subprocess.run(
        ["gh", "api", path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
        text=True,
    )
    return result.returncode == 0


def list_response_items(user: str, include_private: bool, page: int) -> list[dict[str, Any]]:
    if not include_private:
        return gh_api(f"/users/{user}/repos?page={page}&per_page=100")

    try:
        return gh_api(
            f"/user/repos?visibility=all&affiliation=owner&page={page}&per_page=100",
            suppress_stderr=True,
        )
    except subprocess.CalledProcessError:
        response = gh_api(f"/installation/repositories?page={page}&per_page=100")
        return response["repositories"]


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


def matches_filter_paths(full_name: str, filter_paths: list[str]) -> bool:
    if not filter_paths:
        return True
    return any(
        gh_api_ok(f"/repos/{full_name}/contents/{filter_path}")
        for filter_path in filter_paths
    )


def main() -> int:
    args = parse_args()
    user = args.user

    owner_type = subprocess.check_output(
        ["gh", "api", f"/users/{user}", "--jq", ".type"], text=True
    ).strip()
    if owner_type != "User":
        print(f"Expected GitHub user, got: {owner_type}", file=sys.stderr)
        return 1

    include_public = args.public == "true"
    include_private = args.private == "true"
    include_forks = args.fork == "true"
    include_archived = args.archived == "true"
    filter_paths = args.filter_paths

    if not include_public and not include_private:
        print("[]")
        return 0

    page = 1
    repositories: list[dict[str, Any]] = []
    while True:
        response_items = list_response_items(user, include_private, page)
        page_repositories = [
            normalize_repository(item)
            for item in response_items
            if normalize_repository(item)["owner"] == user
        ]
        repositories.extend(
            repository
            for repository in page_repositories
            if include_repository(
                repository,
                include_public=include_public,
                include_private=include_private,
                include_forks=include_forks,
                include_archived=include_archived,
            )
        )

        if len(response_items) < 100:
            break
        page += 1

    if filter_paths:
        max_workers = min(16, max(1, len(repositories)))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            matches = list(
                executor.map(
                    lambda repo: matches_filter_paths(repo["full_name"], filter_paths),
                    repositories,
                )
            )
        repositories = [
            repository
            for repository, matched in zip(repositories, matches, strict=False)
            if matched
        ]

    print(json.dumps(repositories, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

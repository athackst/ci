#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
COPIER_PATHS = REPO_ROOT / "copier_update_paths.txt"
OUTPUT_PATH = REPO_ROOT / "docs" / "workflow_status.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate docs/workflow_status.md for managed CI workflows."
    )
    parser.add_argument(
        "--repos-file",
        type=Path,
        required=True,
        help="JSON file containing repository names or repository metadata objects.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=OUTPUT_PATH,
        help="Markdown file to write.",
    )
    return parser.parse_args()


def normalize_repository(record: Any) -> dict[str, Any]:
    if isinstance(record, str):
        owner, _, name = record.partition("/")
        return {
            "owner": owner,
            "name": name or owner,
            "full_name": record,
            "private": False,
            "fork": False,
            "archived": False,
        }

    if not isinstance(record, dict):
        raise ValueError(f"Unsupported repository entry: {record!r}")

    full_name = record.get("full_name", "")
    owner = record.get("owner")
    name = record.get("name")

    if not owner and isinstance(full_name, str) and "/" in full_name:
        owner = full_name.split("/", 1)[0]
    if not name and isinstance(full_name, str) and "/" in full_name:
        name = full_name.split("/", 1)[1]

    if not owner or not name:
        raise ValueError(f"Repository entry is missing owner/name: {record!r}")

    return {
        "owner": owner,
        "name": name,
        "full_name": record.get("full_name", f"{owner}/{name}"),
        "private": bool(record.get("private", False)),
        "fork": bool(record.get("fork", False)),
        "archived": bool(record.get("archived", False)),
    }


def load_matching_repositories(repos_file: Path) -> list[dict[str, Any]]:
    repositories = json.loads(repos_file.read_text())
    normalized = [normalize_repository(record) for record in repositories]
    public_repositories = [
        repository
        for repository in normalized
        if not repository["private"] and not repository["fork"] and not repository["archived"]
    ]

    return sorted(public_repositories, key=lambda repository: repository["name"].lower())


def _retry_delay_seconds(headers: Any, body_text: str) -> int | None:
    retry_after = headers.get("Retry-After") if headers else None
    if retry_after:
        try:
            return max(int(retry_after), 1)
        except ValueError:
            return 1

    remaining = headers.get("X-RateLimit-Remaining") if headers else None
    reset = headers.get("X-RateLimit-Reset") if headers else None
    if remaining == "0" and reset:
        try:
            return max(int(reset) - int(time.time()) + 1, 1)
        except ValueError:
            return 1

    lowered = body_text.lower()
    if "rate limit" in lowered or "secondary rate limit" in lowered:
        return 5
    return None


def graphql_request(query: str, token: str | None, *, allow_token_fallback: bool = True) -> dict[str, Any]:
    payload = json.dumps({"query": query}).encode("utf-8")
    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "workflow-status-generator",
            "Content-Type": "application/json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        request = Request("https://api.github.com/graphql", data=payload, method="POST", headers=headers)

        try:
            with urlopen(request) as response:
                response_body = response.read().decode("utf-8")
                parsed = json.loads(response_body)
                errors = parsed.get("errors") or []
                if errors:
                    messages = "; ".join(
                        error.get("message", "unknown graphql error") for error in errors
                    )
                    delay = _retry_delay_seconds(response.headers, messages)
                    if delay is not None and attempt < max_attempts:
                        print(
                            f"GraphQL rate limit hit; retrying in {delay}s "
                            f"(attempt {attempt}/{max_attempts}).",
                            file=sys.stderr,
                        )
                        time.sleep(delay)
                        continue
                    raise RuntimeError(f"GraphQL query failed: {messages}")

                data = parsed.get("data")
                if not isinstance(data, dict):
                    return {}
                return data
        except HTTPError as error:
            body_text = error.read().decode("utf-8", errors="replace")
            delay = _retry_delay_seconds(error.headers, body_text)
            if delay is not None and attempt < max_attempts:
                print(
                    f"Workflow metadata query throttled; retrying in {delay}s "
                    f"(attempt {attempt}/{max_attempts}).",
                    file=sys.stderr,
                )
                time.sleep(delay)
                continue
            if (
                token
                and allow_token_fallback
                and error.code == 403
                and "rate limit" in body_text.lower()
            ):
                print(
                    "Token rate limit exceeded for GraphQL query; retrying without token for public repos.",
                    file=sys.stderr,
                )
                return graphql_request(query, None, allow_token_fallback=False)
            raise RuntimeError(f"Unable to query workflow metadata: HTTP {error.code}") from error
        except URLError as error:
            raise RuntimeError(f"Unable to query workflow metadata: {error.reason}") from error

    return {}


def list_remote_workflow_files_batched(
    repositories: list[dict[str, Any]], token: str | None, chunk_size: int = 30
) -> dict[str, set[str]]:
    workflows_by_repo: dict[str, set[str]] = {repository["full_name"]: set() for repository in repositories}

    for start in range(0, len(repositories), chunk_size):
        chunk = repositories[start : start + chunk_size]
        fields = []
        for index, repository in enumerate(chunk):
            owner_literal = json.dumps(repository["owner"])
            name_literal = json.dumps(repository["name"])
            fields.append(
                f"""
  repo_{index}: repository(owner: {owner_literal}, name: {name_literal}) {{
    workflows: object(expression: "HEAD:.github/workflows") {{
      __typename
      ... on Tree {{
        entries {{
          name
          type
        }}
      }}
    }}
  }}"""
            )
        query = "query {\n" + "\n".join(fields) + "\n}"
        data = graphql_request(query, token)

        for index, repository in enumerate(chunk):
            key = f"repo_{index}"
            repo_data = data.get(key)
            if not isinstance(repo_data, dict):
                continue

            workflows = repo_data.get("workflows")
            if not isinstance(workflows, dict):
                continue
            if workflows.get("__typename") != "Tree":
                continue

            entries = workflows.get("entries")
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                if entry.get("type") != "blob":
                    continue
                name = entry.get("name")
                if isinstance(name, str):
                    workflows_by_repo[repository["full_name"]].add(name)

    return workflows_by_repo


def main() -> None:
    args = parse_args()
    github_token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    managed_workflows = [
        line.strip()
        for line in COPIER_PATHS.read_text().splitlines()
        if line.strip().startswith(".github/workflows/")
    ]
    matching_repos = load_matching_repositories(args.repos_file)
    workflows_by_repo = list_remote_workflow_files_batched(matching_repos, github_token)

    header_labels = [Path(path).stem for path in managed_workflows]
    lines = [
        "# Workflow Status",
        "",
        "Public repositories using this CI template, with live status badges for the managed workflows listed in `copier_update_paths.txt`.",
        "",
        f"- Repositories shown: {len(matching_repos)}",
        f"- Managed workflows shown: {len(managed_workflows)}",
        "",
        "| Repository | " + " | ".join(header_labels) + " |",
        "| " + " | ".join(["---"] * (len(header_labels) + 1)) + " |",
    ]

    for repository in matching_repos:
        owner = repository["owner"]
        repo = repository["name"]
        remote_workflow_files = workflows_by_repo.get(repository["full_name"], set())
        row = [f"[`{repository['full_name']}`](https://github.com/{repository['full_name']})"]
        for workflow_path in managed_workflows:
            workflow_file = Path(workflow_path).name
            workflow_name = Path(workflow_path).stem
            if workflow_file in remote_workflow_files:
                row.append(
                    f"[![{workflow_name}]"
                    f"(https://github.com/{owner}/{repo}/actions/workflows/{workflow_file}/badge.svg)]"
                    f"(https://github.com/{owner}/{repo}/actions/workflows/{workflow_file})"
                )
            else:
                row.append("-")
        lines.append("| " + " | ".join(row) + " |")

    lines.extend(
        [
            "",
            "> Badges may appear as missing if a workflow has not been added to a repository yet or has never run on `main`.",
            "",
        ]
    )
    args.output_path.write_text("\n".join(lines))


if __name__ == "__main__":
    main()

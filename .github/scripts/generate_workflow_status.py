#!/usr/bin/env python3
"""Generate the managed-repository workflow status page."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

API_BASE = "https://api.github.com"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANAGED_PATHS_FILE = REPO_ROOT / "copier_update_paths.txt"
DEFAULT_OUTPUT_PATH = REPO_ROOT / "workflow_status.md"


@dataclass(frozen=True)
class Repository:
    owner: str
    name: str

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate workflow_status.md for managed CI workflows."
    )
    parser.add_argument(
        "--owner",
        action="append",
        default=[],
        help=(
            "GitHub user or organization owner to inspect. May be provided multiple "
            "times."
        ),
    )
    parser.add_argument(
        "--answers-file",
        default=".copier-answers.ci.yml",
        help="Repository path identifying a managed Copier repository.",
    )
    parser.add_argument(
        "--managed-paths-file",
        type=Path,
        default=DEFAULT_MANAGED_PATHS_FILE,
        help="File containing managed repository paths.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Markdown file to write.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=30,
        help="Maximum repositories included in each GraphQL query.",
    )
    return parser.parse_args()


def resolve_owners(cli_owners: list[str]) -> list[str]:
    owners: list[str] = []
    for candidate in cli_owners:
        owner = candidate.strip()
        if not owner:
            continue
        if not all(character.isalnum() or character in "._-" for character in owner):
            raise ValueError(f"Invalid repository owner: {owner}")
        if owner not in owners:
            owners.append(owner)
    if not owners:
        raise ValueError("No repository owners configured.")
    return owners


def retry_delay_seconds(headers: Any, body_text: str) -> int | None:
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


class GitHubClient:
    def __init__(self, token: str | None) -> None:
        self.token = token

    def _headers(self, *, graphql: bool = False) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "workflow-status-generator",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if graphql:
            headers["Content-Type"] = "application/json"
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def get_json(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> Any:
        query = f"?{urlencode(params)}" if params else ""
        request = Request(
            f"{API_BASE}{path}{query}",
            headers=self._headers(),
        )
        try:
            with urlopen(request) as response:
                return json.load(response)
        except HTTPError as error:
            raise RuntimeError(
                f"GitHub API request failed for {path}: HTTP {error.code}"
            ) from error
        except URLError as error:
            raise RuntimeError(
                f"GitHub API request failed for {path}: {error.reason}"
            ) from error

    def graphql(
        self,
        query: str,
        *,
        allow_token_fallback: bool = True,
    ) -> dict[str, Any]:
        payload = json.dumps({"query": query}).encode("utf-8")
        max_attempts = 5
        for attempt in range(1, max_attempts + 1):
            request = Request(
                f"{API_BASE}/graphql",
                data=payload,
                method="POST",
                headers=self._headers(graphql=True),
            )
            try:
                with urlopen(request) as response:
                    response_body = response.read().decode("utf-8")
                    parsed = json.loads(response_body)
                    errors = parsed.get("errors") or []
                    if errors:
                        messages = "; ".join(
                            error.get("message", "unknown GraphQL error")
                            for error in errors
                        )
                        delay = retry_delay_seconds(response.headers, messages)
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
                    return data if isinstance(data, dict) else {}
            except HTTPError as error:
                body_text = error.read().decode("utf-8", errors="replace")
                delay = retry_delay_seconds(error.headers, body_text)
                if delay is not None and attempt < max_attempts:
                    print(
                        f"Workflow metadata query throttled; retrying in {delay}s "
                        f"(attempt {attempt}/{max_attempts}).",
                        file=sys.stderr,
                    )
                    time.sleep(delay)
                    continue
                if (
                    self.token
                    and allow_token_fallback
                    and error.code == 403
                    and "rate limit" in body_text.lower()
                ):
                    print(
                        "Token rate limit exceeded; retrying public workflow metadata "
                        "without authentication.",
                        file=sys.stderr,
                    )
                    return GitHubClient(None).graphql(
                        query,
                        allow_token_fallback=False,
                    )
                raise RuntimeError(
                    f"Unable to query workflow metadata: HTTP {error.code}"
                ) from error
            except URLError as error:
                raise RuntimeError(
                    f"Unable to query workflow metadata: {error.reason}"
                ) from error

        return {}


def discover_repositories(
    owners: list[str],
    client: GitHubClient,
) -> list[Repository]:
    repositories: dict[str, Repository] = {}
    for owner in owners:
        owner_type = client.get_json(f"/users/{quote(owner)}").get("type")
        if owner_type == "Organization":
            path = f"/orgs/{quote(owner)}/repos"
        elif owner_type == "User":
            path = f"/users/{quote(owner)}/repos"
        else:
            raise ValueError(
                f"Expected GitHub user or organization for {owner}, got: {owner_type}"
            )

        page = 1
        while True:
            items = client.get_json(
                path,
                params={
                    "page": page,
                    "per_page": 100,
                },
            )
            if not isinstance(items, list):
                raise RuntimeError(f"Unexpected repository response for {owner}")

            for item in items:
                if not isinstance(item, dict):
                    continue
                item_owner = (item.get("owner") or {}).get("login", owner)
                if item_owner.lower() != owner.lower():
                    continue
                if item.get("private") or item.get("fork") or item.get("archived"):
                    continue
                name = item.get("name")
                if not isinstance(name, str) or not name:
                    continue
                repository = Repository(owner=item_owner, name=name)
                repositories[repository.full_name.lower()] = repository

            if len(items) < 100:
                break
            page += 1

    return sorted(
        repositories.values(),
        key=lambda repository: repository.full_name.lower(),
    )


def inspect_managed_repositories(
    repositories: list[Repository],
    client: GitHubClient,
    *,
    answers_file: str,
    chunk_size: int,
) -> tuple[list[Repository], dict[str, set[str]]]:
    if chunk_size < 1:
        raise ValueError("chunk-size must be greater than zero")

    managed_repositories: list[Repository] = []
    workflows_by_repo: dict[str, set[str]] = {}
    answers_expression = json.dumps(f"HEAD:{answers_file}")

    for start in range(0, len(repositories), chunk_size):
        chunk = repositories[start : start + chunk_size]
        fields = []
        for index, repository in enumerate(chunk):
            fields.append(
                f"""
  repo_{index}: repository(
    owner: {json.dumps(repository.owner)}
    name: {json.dumps(repository.name)}
  ) {{
    answers: object(expression: {answers_expression}) {{
      __typename
    }}
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
        data = client.graphql("query {\n" + "\n".join(fields) + "\n}")

        for index, repository in enumerate(chunk):
            repo_data = data.get(f"repo_{index}")
            if not isinstance(repo_data, dict):
                continue
            answers = repo_data.get("answers")
            if not isinstance(answers, dict) or answers.get("__typename") != "Blob":
                continue

            workflow_files: set[str] = set()
            workflows = repo_data.get("workflows")
            if isinstance(workflows, dict) and workflows.get("__typename") == "Tree":
                entries = workflows.get("entries")
                if isinstance(entries, list):
                    for entry in entries:
                        if (
                            isinstance(entry, dict)
                            and entry.get("type") == "blob"
                            and isinstance(entry.get("name"), str)
                        ):
                            workflow_files.add(entry["name"])

            managed_repositories.append(repository)
            workflows_by_repo[repository.full_name] = workflow_files

    return managed_repositories, workflows_by_repo


def load_managed_workflows(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text().splitlines()
        if line.strip().startswith(".github/workflows/")
    ]


def render_status(
    repositories: list[Repository],
    workflows_by_repo: dict[str, set[str]],
    managed_workflows: list[str],
) -> str:
    header_labels = [Path(path).stem for path in managed_workflows]
    lines = [
        "# Workflow Status",
        "",
        "Public repositories using this CI template, with live status badges for "
        "the managed workflows listed in `copier_update_paths.txt`.",
        "",
        f"- Repositories shown: {len(repositories)}",
        f"- Managed workflows shown: {len(managed_workflows)}",
        "",
        "| Repository | " + " | ".join(header_labels) + " |",
        "| " + " | ".join(["---"] * (len(header_labels) + 1)) + " |",
    ]

    for repository in repositories:
        remote_workflow_files = workflows_by_repo.get(repository.full_name, set())
        row = [
            f"[`{repository.full_name}`]"
            f"(https://github.com/{repository.full_name})"
        ]
        for workflow_path in managed_workflows:
            workflow_file = Path(workflow_path).name
            workflow_name = Path(workflow_path).stem
            if workflow_file in remote_workflow_files:
                row.append(
                    f"[![{workflow_name}]"
                    f"(https://github.com/{repository.full_name}/actions/workflows/"
                    f"{workflow_file}/badge.svg)]"
                    f"(https://github.com/{repository.full_name}/actions/workflows/"
                    f"{workflow_file})"
                )
            else:
                row.append("-")
        lines.append("| " + " | ".join(row) + " |")

    lines.extend(
        [
            "",
            "> Badges may appear as missing if a workflow has not been added to a "
            "repository yet or has never run on `main`.",
            "",
        ]
    )
    return "\n".join(lines)


def write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        delete=False,
    ) as output:
        output.write(content)
        temporary_path = Path(output.name)
    temporary_path.replace(path)


def main() -> int:
    args = parse_args()
    try:
        owners = resolve_owners(
            args.owner,
        )
        token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
        client = GitHubClient(token)
        repositories = discover_repositories(owners, client)
        managed_repositories, workflows_by_repo = inspect_managed_repositories(
            repositories,
            client,
            answers_file=args.answers_file,
            chunk_size=args.chunk_size,
        )
        managed_workflows = load_managed_workflows(args.managed_paths_file)
        write_atomic(
            args.output_path,
            render_status(
                managed_repositories,
                workflows_by_repo,
                managed_workflows,
            ),
        )
    except (RuntimeError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
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
    parser.add_argument(
        "--visibility",
        choices=["public", "private", "all"],
        default="public",
        help="Repository visibility to include in the status page.",
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


def load_matching_repositories(
    repos_file: Path, visibility: str
) -> list[dict[str, Any]]:
    repositories = json.loads(repos_file.read_text())
    normalized = [normalize_repository(record) for record in repositories]
    matching_repositories = [
        repository
        for repository in normalized
        if not repository["fork"] and not repository["archived"]
    ]

    if visibility == "public":
        filtered_repositories = [
            repository for repository in matching_repositories if not repository["private"]
        ]
    elif visibility == "private":
        filtered_repositories = [
            repository for repository in matching_repositories if repository["private"]
        ]
    else:
        filtered_repositories = matching_repositories

    return sorted(filtered_repositories, key=lambda repository: repository["name"].lower())


def main() -> None:
    args = parse_args()
    managed_workflows = [
        line.strip()
        for line in COPIER_PATHS.read_text().splitlines()
        if line.strip().startswith(".github/workflows/")
    ]
    matching_repos = load_matching_repositories(args.repos_file, args.visibility)

    header_labels = [Path(path).stem for path in managed_workflows]
    lines = [
        "# Workflow Status",
        "",
        f"{args.visibility.capitalize()} repositories using this CI template, with live status badges for the managed workflows listed in `copier_update_paths.txt`."
        if args.visibility != "all"
        else "Repositories using this CI template, with live status badges for the managed workflows listed in `copier_update_paths.txt`.",
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
        row = [f"[`{repository['full_name']}`](https://github.com/{repository['full_name']})"]
        for workflow_path in managed_workflows:
            workflow_file = Path(workflow_path).name
            workflow_name = Path(workflow_path).stem
            row.append(
                f"[![{workflow_name}]"
                f"(https://github.com/{owner}/{repo}/actions/workflows/{workflow_file}/badge.svg?branch=main)]"
                f"(https://github.com/{owner}/{repo}/actions/workflows/{workflow_file})"
            )
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

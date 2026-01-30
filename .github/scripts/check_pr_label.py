#!/usr/bin/env python3
import ast
import json
import os
import sys
import urllib.request
from fnmatch import fnmatch
from pathlib import Path


def load_label_patterns(path: Path):
    patterns = []
    for line_no, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            print(f"Malformed line {line_no}: missing ':'", file=sys.stderr)
            continue
        label, rest = line.split(":", 1)
        label = label.strip()
        list_text = rest.strip()
        if not list_text.startswith("["):
            print(
                f"Malformed line {line_no}: expected list after label '{label}'",
                file=sys.stderr,
            )
            continue
        try:
            values = ast.literal_eval(list_text)
        except (ValueError, SyntaxError):
            print(f"Malformed line {line_no}: invalid list syntax", file=sys.stderr)
            continue
        if not isinstance(values, list):
            print(f"Malformed line {line_no}: expected list", file=sys.stderr)
            continue
        patterns.append((label, [str(item) for item in values]))
    return patterns


def expected_labels(branch: str, patterns):
    expected = []
    seen = set()
    for label, globs in patterns:
        for glob in globs:
            if fnmatch(branch, glob):
                if label not in seen:
                    expected.append(label)
                    seen.add(label)
                break
    return expected


def fetch_labels(repo: str, pr_number: str, token: str):
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/labels"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "pr-labeler-test",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    branch = os.environ.get("PR_LABELER_BRANCH", "")
    repo = os.environ.get("PR_LABELER_REPO", "")
    pr_number = os.environ.get("PR_LABELER_PR", "")
    token = os.environ.get("GITHUB_TOKEN", "")

    if not branch or not repo or not pr_number or not token:
        print(
            "Missing required env vars: PR_LABELER_BRANCH, PR_LABELER_REPO, PR_LABELER_PR, GITHUB_TOKEN"
        )
        return 1

    config_path = Path("actions/pr-labeler/pr-labeler.yml")
    if not config_path.exists():
        print(f"Missing label config at {config_path}")
        return 1

    patterns = load_label_patterns(config_path)
    expected = expected_labels(branch, patterns)

    if not expected:
        print(f"No matching label for branch '{branch}'; skipping assertion.")
        return 0

    labels = fetch_labels(repo, pr_number, token)
    names = [label.get("name", "") for label in labels if isinstance(label, dict)]

    missing = [label for label in expected if label not in names]
    if not missing:
        print("All expected labels are present.")
        return 0

    print(f"Missing expected labels: {', '.join(missing)}")
    print("Labels:")
    print(json.dumps(labels, indent=2))
    return 1


if __name__ == "__main__":
    sys.exit(main())

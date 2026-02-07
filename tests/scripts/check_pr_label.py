#!/usr/bin/env python3
import ast
import json
import os
import re
import sys
import urllib.request
from fnmatch import fnmatch
from pathlib import Path


def load_config_labels(path: Path):
    labels = []
    seen = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        # Match YAML top-level keys like: my-label:
        if raw_line.startswith((" ", "\t", "#")):
            continue
        match = re.match(r"^([^:#][^:]*)\s*:\s*$", raw_line)
        if not match:
            continue
        label = match.group(1).strip()
        if label and label not in seen:
            labels.append(label)
            seen.add(label)
    return labels


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
    branch = os.environ.get("PR_LABELER_BRANCH", os.environ.get("GITHUB_HEAD_REF", ""))
    repo = os.environ.get("PR_LABELER_REPO", os.environ.get("GITHUB_REPOSITORY", ""))
    pr_number = os.environ.get("PR_LABELER_PR", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    config_path = os.environ.get(
        "PR_LABELER_CONFIG_PATH", "actions/pr-labeler/pr-labeler.yml"
    )

    config_path = Path(config_path)
    if not config_path.exists():
        print(f"Missing label config at {config_path}")
        return 1

    configured_labels = load_config_labels(config_path)
    patterns = load_label_patterns(config_path)
    expected = expected_labels(branch, patterns) if branch and patterns else configured_labels
    expected_json = json.dumps(expected)
    print(f"EXPECTED_LABELS_JSON={expected_json}")

    if not expected:
        print("No expected labels found; skipping assertion.")
        return 0

    if not repo or not pr_number or not token:
        print(
            "Skipping API assertion because PR_LABELER_REPO, PR_LABELER_PR, or GITHUB_TOKEN is missing."
        )
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

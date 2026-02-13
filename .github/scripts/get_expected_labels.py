#!/usr/bin/env python3
import argparse
import ast
import json
import os
import re
import sys
from fnmatch import fnmatch
from pathlib import Path

def load_config_labels(path: Path):
    labels = []
    seen = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
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


def uses_changed_files_rules(path: Path):
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith(("changed-files:", "- changed-files:", "any-glob-to-any-file:")):
            return True
    return False


def load_label_patterns(path: Path):
    pattern_map = {}
    current_label = None

    for line_no, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if not raw_line.startswith((" ", "\t")):
            if ":" not in line:
                continue
            label, rest = line.split(":", 1)
            label = label.strip()
            rest = rest.strip()
            current_label = label
            pattern_map.setdefault(current_label, [])

            if rest.startswith("["):
                try:
                    values = ast.literal_eval(rest)
                except (ValueError, SyntaxError):
                    print(
                        f"Malformed line {line_no}: invalid list syntax for label '{label}'",
                        file=sys.stderr,
                    )
                    continue
                if isinstance(values, list):
                    pattern_map[current_label].extend(str(item) for item in values)
            continue

        if current_label is None or "any-glob-to-any-file:" not in line:
            continue

        _, list_text = line.split("any-glob-to-any-file:", 1)
        list_text = list_text.strip()
        if not list_text.startswith("["):
            continue
        try:
            values = ast.literal_eval(list_text)
        except (ValueError, SyntaxError):
            print(
                f"Malformed line {line_no}: invalid any-glob-to-any-file list syntax",
                file=sys.stderr,
            )
            continue
        if isinstance(values, list):
            pattern_map[current_label].extend(str(item) for item in values)

    return [(label, globs) for label, globs in pattern_map.items() if globs]


def expected_labels_from_branch(branch: str, patterns):
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


def compute_expected_labels(config_path: Path, branch: str):
    configured_labels = load_config_labels(config_path)
    patterns = load_label_patterns(config_path)

    if uses_changed_files_rules(config_path):
        return configured_labels

    if branch and patterns:
        return expected_labels_from_branch(branch, patterns)

    return configured_labels


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Extract expected PR labels from a labeler config. "
            "Requires the GITHUB_HEAD_REF environment variable for branch matching."
        )
    )
    parser.add_argument("config_path", help="Path to the labeler config file.")
    return parser.parse_args()


def main():
    args = parse_args()
    config_path = Path(args.config_path)
    branch = os.environ.get("GITHUB_HEAD_REF", "")

    if not branch:
        print("Missing required environment variable: GITHUB_HEAD_REF", file=sys.stderr)
        return 1

    if not config_path.exists():
        print(f"Missing label config at {config_path}", file=sys.stderr)
        return 1

    expected = compute_expected_labels(config_path, branch)
    print(json.dumps(expected))
    return 0


if __name__ == "__main__":
    sys.exit(main())

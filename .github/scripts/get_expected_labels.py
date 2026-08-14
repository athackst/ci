#!/usr/bin/env python3
"""Emit the labels a labeler config guarantees for the current pull request.

Prints a JSON list of the labels that actions/labeler is certain to apply
given the branch names in GITHUB_HEAD_REF and GITHUB_BASE_REF. Conditions
that depend on information unavailable here, such as changed-files globs
narrower than a match-everything pattern, are treated as not guaranteed, so
the output is a subset of what the labeler applies and is safe to assert as
required labels.

Matches actions/labeler v5 semantics: branch patterns are regular
expressions tested with a partial match, top-level match objects under a
label are OR'd, and keys within one match object are AND'd.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

import yaml

# Every pull request changes at least one file, so these globs always match.
UNIVERSAL_GLOBS = {"**", "**/*"}
GLOB_KEYS = (
    "any-glob-to-any-file",
    "all-globs-to-all-files",
    "all-globs-to-any-file",
    "any-glob-to-all-files",
)


class ConfigError(ValueError):
    pass


def as_list(value):
    return value if isinstance(value, list) else [value]


def branch_matches(label, patterns, branch):
    for pattern in as_list(patterns):
        try:
            if re.search(str(pattern), branch):
                return True
        except re.error as err:
            raise ConfigError(f"{label}: invalid branch pattern {pattern!r}: {err}")
    return False


def changed_files_guaranteed(matchers):
    for matcher in as_list(matchers):
        if not isinstance(matcher, dict):
            continue
        for key in GLOB_KEYS:
            globs = as_list(matcher.get(key, []))
            if any(str(glob) in UNIVERSAL_GLOBS for glob in globs):
                return True
    return False


def condition_guaranteed(label, condition, head_ref, base_ref):
    if not isinstance(condition, dict):
        return False

    results = []
    for key, value in condition.items():
        if key == "head-branch":
            results.append(branch_matches(label, value, head_ref))
        elif key == "base-branch":
            results.append(bool(base_ref) and branch_matches(label, value, base_ref))
        elif key == "changed-files":
            results.append(changed_files_guaranteed(value))
        elif key == "any":
            results.append(
                any(condition_guaranteed(label, c, head_ref, base_ref) for c in as_list(value))
            )
        elif key == "all":
            results.append(
                all(condition_guaranteed(label, c, head_ref, base_ref) for c in as_list(value))
            )
        # Other keys are label metadata such as description and color.

    return bool(results) and all(results)


def load_labels(config_path: Path):
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ConfigError("Label configuration must be a mapping.")
    labels = data.get("labels")
    if not isinstance(labels, dict):
        labels = data
    return labels


def compute_expected_labels(config_path: Path, head_ref: str, base_ref: str):
    expected = []
    for label, conditions in load_labels(config_path).items():
        if not isinstance(conditions, list):
            raise ConfigError(f"{label}: conditions must be a list")
        if any(
            condition_guaranteed(label, condition, head_ref, base_ref)
            for condition in conditions
        ):
            expected.append(label)
    return expected


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Extract the labels a labeler config guarantees for a pull request. "
            "Requires the GITHUB_HEAD_REF environment variable; uses "
            "GITHUB_BASE_REF for base-branch rules when set."
        )
    )
    parser.add_argument("config_path", help="Path to the labeler config file.")
    return parser.parse_args()


def main():
    args = parse_args()
    config_path = Path(args.config_path)
    head_ref = os.environ.get("GITHUB_HEAD_REF", "")
    base_ref = os.environ.get("GITHUB_BASE_REF", "")

    if not head_ref:
        print("Missing required environment variable: GITHUB_HEAD_REF", file=sys.stderr)
        return 1

    if not config_path.exists():
        print(f"Missing label config at {config_path}", file=sys.stderr)
        return 1

    try:
        expected = compute_expected_labels(config_path, head_ref, base_ref)
    except (ConfigError, yaml.YAMLError) as err:
        print(f"Invalid label config {config_path}: {err}", file=sys.stderr)
        return 1

    print(json.dumps(expected))
    return 0


if __name__ == "__main__":
    sys.exit(main())

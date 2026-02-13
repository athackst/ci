#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

from release_drafter_config import load_release_drafter_config


def parse_version(tag: str):
    if not tag:
        return (0, 0, 0)
    match = re.match(r"^v?(\d+)\.(\d+)\.(\d+)$", tag.strip())
    if not match:
        return (0, 0, 0)
    return tuple(int(x) for x in match.groups())


def is_semver_tag(tag: str):
    return re.match(r"^v\d+\.\d+\.\d+$", (tag or "").strip()) is not None


def bump_version(version, bump):
    major, minor, patch = version
    if bump == "major":
        return (major + 1, 0, 0)
    if bump == "minor":
        return (major, minor + 1, 0)
    return (major, minor, patch + 1)


def select_bump(labels, version_resolver):
    if labels & version_resolver["major"]:
        return "major"
    if labels & version_resolver["minor"]:
        return "minor"
    return "patch"


def resolve_base_ref(tags, first_commit):
    if tags:
        return tags[0], True
    return first_commit, False


def apply_template(template, version):
    return template.replace("$RESOLVED_VERSION", version)


def build_release(version, name_template, tag_template):
    tag_name = apply_template(tag_template, version)
    release_name = apply_template(name_template, version)
    return tag_name, release_name


def get_tags():
    result = subprocess.run(
        ["git", "tag", "--sort=-version:refname"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def get_latest_semver_tag(tags):
    for tag in tags:
        if is_semver_tag(tag):
            return tag
    return None


def get_first_commit():
    result = subprocess.run(
        ["git", "rev-list", "--max-parents=0", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    commits = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not commits:
        raise RuntimeError("Unable to resolve first commit.")
    return commits[-1]


def run_base():
    tags = get_tags()
    latest_semver_tag = get_latest_semver_tag(tags)
    first_commit = get_first_commit()
    from_ref, used_tag = resolve_base_ref(
        [latest_semver_tag] if latest_semver_tag else [], first_commit
    )
    if used_tag:
        print(f"Using latest semver tag as changelog base: {from_ref}", file=sys.stderr)
    else:
        print(
            f"No semver tags found. Using first commit as changelog base: {from_ref}",
            file=sys.stderr,
        )
    return {"from_ref": from_ref}


def run_next():
    token = os.environ["GH_TOKEN"]
    repo = os.environ["REPO"]
    from_tag = os.environ.get("FROM_TAG", "")
    pr_ids_raw = os.environ.get("PR_IDS", "")
    config_path = os.environ.get(
        "RELEASE_DRAFTER_CONFIG",
        str(Path(__file__).with_name("release-drafter.yml")),
    )
    config = load_release_drafter_config(config_path)
    version_resolver = config["version_resolver"]
    exclude_labels = config["exclude_labels"]
    name_template = config["name_template"]
    tag_template = config["tag_template"]

    pr_ids = [x.strip() for x in pr_ids_raw.split(",") if x.strip()]
    labels = set()
    for pr_id in pr_ids:
        url = f"https://api.github.com/repos/{repo}/pulls/{pr_id}"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "release-draft-action",
            },
        )
        with urllib.request.urlopen(req) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        pr_labels = {
            label.get("name")
            for label in payload.get("labels", [])
            if label.get("name")
        }
        if pr_labels & exclude_labels:
            continue
        labels.update(pr_labels)

    bump = select_bump(labels, version_resolver)

    next_version = bump_version(parse_version(from_tag), bump)
    version = f"{next_version[0]}.{next_version[1]}.{next_version[2]}"
    tag_name, release_name = build_release(version, name_template, tag_template)
    return {
        "tag_name": tag_name,
        "release_name": release_name,
        "resolved_version": version,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        choices=["base", "next"],
        required=True,
        help="Resolver mode: base resolves from_ref, next resolves tag_name/release_name.",
    )
    args = parser.parse_args()
    if args.mode == "base":
        result = run_base()
    else:
        result = run_next()
    print(json.dumps(result))


if __name__ == "__main__":
    main()

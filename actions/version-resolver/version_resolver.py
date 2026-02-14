#!/usr/bin/env python3
import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from version_config import load_version_config


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
        return tags[0]
    return first_commit


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


def get_commit_range(from_ref, to_ref):
    result = subprocess.run(
        ["git", "rev-list", f"{from_ref}..{to_ref}"],
        check=True,
        capture_output=True,
        text=True,
    )
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def gh_get(url, token, accept="application/vnd.github+json"):
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": accept,
            "User-Agent": "version-resolver-action",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_merged_prs_from_compare(repo, token, from_ref, to_ref):
    compare_url = f"https://api.github.com/repos/{repo}/compare/{from_ref}...{to_ref}"
    compare_data = gh_get(compare_url, token)
    commits = compare_data.get("commits", [])

    if compare_data.get("total_commits", len(commits)) > len(commits):
        raise RuntimeError("Compare response is truncated; use pagination fallback.")

    prs_by_number = {}
    for commit in commits:
        sha = commit.get("sha")
        if not sha:
            continue
        pulls_url = f"https://api.github.com/repos/{repo}/commits/{sha}/pulls"
        pulls = gh_get(
            pulls_url,
            token,
            accept="application/vnd.github+json, application/vnd.github.groot-preview+json",
        )
        if not isinstance(pulls, list):
            continue
        for pr in pulls:
            number = pr.get("number")
            if not number or not pr.get("merged_at"):
                continue
            prs_by_number[number] = pr

    return list(prs_by_number.values())


def fetch_merged_prs_from_pagination(repo, token, commit_shas):
    if not commit_shas:
        return []

    prs = []
    page = 1
    while True:
        url = f"https://api.github.com/repos/{repo}/pulls?state=closed&per_page=100&page={page}"
        data = gh_get(url, token)
        if not data:
            break

        for pr in data:
            if not pr.get("merged_at"):
                continue
            merge_sha = pr.get("merge_commit_sha")
            if merge_sha in commit_shas:
                prs.append(pr)
        page += 1

    return prs


def fetch_merged_prs(repo, token, from_ref, to_ref, commit_shas):
    try:
        prs = fetch_merged_prs_from_compare(repo, token, from_ref, to_ref)
        if prs:
            return prs
    except urllib.error.HTTPError as exc:
        print(
            f"Compare-based PR discovery failed ({exc.code}); falling back to pagination.",
            file=sys.stderr,
        )
    except Exception:
        print("Compare-based PR discovery failed; falling back to pagination.", file=sys.stderr)

    return fetch_merged_prs_from_pagination(repo, token, commit_shas)


def pr_labels(pr):
    return {label.get("name") for label in pr.get("labels", []) if label.get("name")}


def compact_pr(pr):
    return {
        "number": pr.get("number"),
        "title": pr.get("title"),
        "html_url": pr.get("html_url"),
        "merged_at": pr.get("merged_at"),
        "merge_commit_sha": pr.get("merge_commit_sha"),
        "labels": sorted(pr_labels(pr)),
    }


def resolve_all(config_path, repo, token, to_ref):
    tags = get_tags()
    latest_semver_tag = get_latest_semver_tag(tags)
    from_ref = resolve_base_ref(
        [latest_semver_tag] if latest_semver_tag else [],
        get_first_commit(),
    )

    config = load_version_config(config_path)
    commit_shas = get_commit_range(from_ref, to_ref)
    prs = fetch_merged_prs(repo, token, from_ref, to_ref, commit_shas)

    labels = set()
    for pr in prs:
        labels.update(pr_labels(pr))

    bump = select_bump(labels, config["version_resolver"])
    current = parse_version(from_ref)
    next_major, next_minor, next_patch = bump_version(current, bump)
    resolved_version = f"{next_major}.{next_minor}.{next_patch}"

    return {
        "from_ref": from_ref,
        "to_ref": to_ref,
        "pr_info": {
            "pull_requests": [compact_pr(pr) for pr in prs],
            "labels": sorted(labels),
        },
        "resolved_version": resolved_version,
        "major_version": str(next_major),
        "minor_version": str(next_minor),
        "patch_version": str(next_patch),
    }


def to_line(result):
    lines = []
    key_map = {
        "from-ref": "from_ref",
        "resolved-version": "resolved_version",
        "major-version": "major_version",
        "minor-version": "minor_version",
        "patch-version": "patch_version",
    }
    for output_key, result_key in key_map.items():
        value = result.get(result_key)
        if value is not None:
            lines.append(f"{output_key}={value}")
    return "\n".join(lines)


def write_data_file(result, output_path):
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)


def main():
    parser = argparse.ArgumentParser(
        description="Resolve base ref and next semantic version from version-resolver config."
    )
    parser.add_argument(
        "--config-path",
        default=str(Path(__file__).with_name("versions.yml")),
        help="Path to versions.yml config file.",
    )
    parser.add_argument("--repo", required=True, help="owner/repo for PR lookup.")
    parser.add_argument("--gh-token", required=True, help="GitHub token for API requests.")
    parser.add_argument("--to-ref", default="HEAD", help="Target ref for range comparison.")
    parser.add_argument(
        "--output-path",
        default="",
        help="Optional file path to write full resolver JSON data.",
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "line"],
        default="json",
        help="Output format.",
    )

    args = parser.parse_args()
    result = resolve_all(args.config_path, args.repo, args.gh_token, args.to_ref)
    if args.output_path:
        write_data_file(result, args.output_path)

    if args.output_format == "line":
        print(to_line(result))
    else:
        print(json.dumps(result))


if __name__ == "__main__":
    main()

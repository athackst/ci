#!/usr/bin/env python3
import argparse
import json
import os
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
    return re.match(r"^v?\d+\.\d+\.\d+$", (tag or "").strip()) is not None


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


def get_remote_tags(remote="origin"):
    result = subprocess.run(
        ["git", "ls-remote", "--tags", "--refs", remote],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or f"git ls-remote failed for {remote}"
        print(f"Unable to inspect remote tags: {message}", file=sys.stderr)
        return set()

    tags = set()
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) != 2:
            continue
        ref = parts[1]
        if ref.startswith("refs/tags/"):
            tags.add(ref.removeprefix("refs/tags/"))
    return tags


def is_shallow_repository():
    result = subprocess.run(
        ["git", "rev-parse", "--is-shallow-repository"],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip().lower() == "true"


def fetch_tags(remote="origin"):
    command = ["git", "fetch", "--tags", "--force", "--prune", remote]
    if is_shallow_repository():
        command.insert(-1, "--unshallow")

    subprocess.run(command, check=True)


def ensure_tags_available(remote="origin"):
    shallow_repository = is_shallow_repository()
    remote_tags = get_remote_tags(remote)
    if not remote_tags and not shallow_repository:
        return

    local_tags = set(get_tags())
    missing_tags = remote_tags - local_tags
    if not missing_tags and not shallow_repository:
        print("Local checkout already has remote tags and full history.", file=sys.stderr)
        return

    reasons = []
    if missing_tags:
        reasons.append(f"{len(missing_tags)} missing tag(s)")
    if shallow_repository:
        reasons.append("shallow history")
    print(f"Fetching tags and history for version resolution ({', '.join(reasons)}).", file=sys.stderr)
    fetch_tags(remote)


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


def gh_graphql(query, variables, token):
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "version-resolver-action",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as resp:
        body = json.loads(resp.read().decode("utf-8"))

    if body.get("errors"):
        messages = "; ".join(error.get("message", "unknown graphql error") for error in body["errors"])
        raise RuntimeError(f"GraphQL query failed: {messages}")
    return body.get("data", {})


def get_ref_commit_date(ref):
    result = subprocess.run(
        ["git", "show", "-s", "--format=%cI", ref],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def iso_date(value):
    if not value:
        return ""
    return value.split("T", 1)[0]


def fetch_merged_prs_from_graphql_search(repo, token, from_ref, to_ref, commit_shas):
    if not commit_shas:
        return []

    from_date = iso_date(get_ref_commit_date(from_ref))
    to_date = iso_date(get_ref_commit_date(to_ref))
    search_query = f"repo:{repo} is:pr is:merged merged:{from_date}..{to_date}"

    query = """
query($searchQuery: String!, $after: String) {
  search(query: $searchQuery, type: ISSUE, first: 100, after: $after) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on PullRequest {
        number
        title
        url
        mergedAt
        mergeCommit {
          oid
        }
        labels(first: 100) {
          nodes {
            name
          }
        }
      }
    }
  }
}
"""

    prs_by_number = {}
    cursor = None
    while True:
        data = gh_graphql(query, {"searchQuery": search_query, "after": cursor}, token)
        search = data.get("search", {})
        nodes = search.get("nodes", [])
        for node in nodes:
            if not isinstance(node, dict):
                continue
            number = node.get("number")
            merge_commit_sha = (node.get("mergeCommit") or {}).get("oid")
            if not number or not merge_commit_sha:
                continue
            if merge_commit_sha not in commit_shas:
                continue

            label_nodes = (node.get("labels") or {}).get("nodes", [])
            prs_by_number[number] = {
                "number": number,
                "title": node.get("title"),
                "html_url": node.get("url"),
                "merged_at": node.get("mergedAt"),
                "merge_commit_sha": merge_commit_sha,
                "labels": [
                    {"name": label.get("name")}
                    for label in label_nodes
                    if isinstance(label, dict) and label.get("name")
                ],
            }

        page_info = search.get("pageInfo") or {}
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")

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
        prs = fetch_merged_prs_from_graphql_search(repo, token, from_ref, to_ref, commit_shas)
        if prs:
            return prs
    except urllib.error.HTTPError as exc:
        print(
            f"GraphQL-based PR discovery failed ({exc.code}); falling back to pagination.",
            file=sys.stderr,
        )
    except Exception:
        print("GraphQL-based PR discovery failed; falling back to pagination.", file=sys.stderr)

    return fetch_merged_prs_from_pagination(repo, token, commit_shas)


def get_current_pr_from_event(repo):
    if os.getenv("GITHUB_EVENT_NAME") != "pull_request":
        return None

    event_path = os.getenv("GITHUB_EVENT_PATH")
    if not event_path:
        return None

    with open(event_path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)

    pr = payload.get("pull_request")
    if not isinstance(pr, dict):
        return None

    base_full_name = ((pr.get("base") or {}).get("repo") or {}).get("full_name")
    if isinstance(base_full_name, str) and base_full_name.lower() != repo.lower():
        return None

    labels = [
        {"name": label.get("name")}
        for label in pr.get("labels", [])
        if isinstance(label, dict) and label.get("name")
    ]

    return {
        "number": pr.get("number"),
        "title": pr.get("title"),
        "html_url": pr.get("html_url"),
        "merged_at": pr.get("merged_at"),
        "merge_commit_sha": pr.get("merge_commit_sha"),
        "labels": labels,
    }


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
    ensure_tags_available()
    tags = get_tags()
    latest_semver_tag = get_latest_semver_tag(tags)
    from_ref = resolve_base_ref(
        [latest_semver_tag] if latest_semver_tag else [],
        get_first_commit(),
    )
    if latest_semver_tag:
        print(f"Found latest semantic version tag: {latest_semver_tag}", file=sys.stderr)
    else:
        print("No semantic version tag found; falling back to first commit.", file=sys.stderr)
    print(f"Resolved changelog base ref: {from_ref}", file=sys.stderr)

    config = load_version_config(config_path)
    commit_shas = get_commit_range(from_ref, to_ref)
    prs = fetch_merged_prs(repo, token, from_ref, to_ref, commit_shas)
    current_pr = get_current_pr_from_event(repo)
    if current_pr:
        current_number = current_pr.get("number")
        existing_numbers = {pr.get("number") for pr in prs if pr.get("number") is not None}
        if current_number not in existing_numbers:
            prs.append(current_pr)

    labels = set()
    for pr in prs:
        labels.update(pr_labels(pr))

    bump = select_bump(labels, config["version_resolver"])
    current = parse_version(from_ref)
    next_major, next_minor, next_patch = bump_version(current, bump)
    resolved_version = f"{next_major}.{next_minor}.{next_patch}"

    return {
        "from_ref": from_ref,
        "latest_semver_tag": latest_semver_tag or "",
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
        "latest-semver-tag": "latest_semver_tag",
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

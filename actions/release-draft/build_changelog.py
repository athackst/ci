#!/usr/bin/env python3
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

from release_drafter_config import load_release_drafter_config


def gh_get(url, token, accept="application/vnd.github+json"):
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": accept,
            "User-Agent": "release-draft-action",
        },
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_commit_range(from_ref, to_ref):
    result = subprocess.run(
        ["git", "rev-list", f"{from_ref}..{to_ref}"],
        check=True,
        capture_output=True,
        text=True,
    )
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


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
    prs.sort(key=lambda pr: pr.get("merged_at") or "")
    return prs


def fetch_merged_prs_from_compare(repo, token, from_ref, to_ref):
    compare_url = f"https://api.github.com/repos/{repo}/compare/{from_ref}...{to_ref}"
    compare_data = gh_get(compare_url, token)
    commits = compare_data.get("commits", [])

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

    prs = list(prs_by_number.values())
    prs.sort(key=lambda pr: pr.get("merged_at") or "")
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


def render_pr_line(pr):
    number = pr["number"]
    title = (pr.get("title") or "").strip()
    url = pr.get("html_url") or ""
    author = (pr.get("user") or {}).get("login") or "unknown"
    return f"- {title} [#{number}]({url}) (@{author})"


def build_changes(prs, config):
    exclude = config["exclude_labels"]
    categories = config["categories"]
    grouped = {idx: [] for idx in range(len(categories))}
    uncategorized = []
    included_pr_ids = []

    for pr in prs:
        labels = pr_labels(pr)
        if labels & exclude:
            continue
        included_pr_ids.append(str(pr["number"]))

        matched = False
        for idx, category in enumerate(categories):
            if labels & set(category["labels"]):
                grouped[idx].append(render_pr_line(pr))
                matched = True
                break
        if not matched:
            uncategorized.append(render_pr_line(pr))

    sections = []
    for idx, category in enumerate(categories):
        lines = grouped[idx]
        if not lines:
            continue
        sections.append(f"{category['title']}\n")
        sections.extend(lines)
        sections.append("")

    if uncategorized:
        sections.append("### Other Changes\n")
        sections.extend(uncategorized)
        sections.append("")

    changes = "\n".join(sections).strip()
    return changes, included_pr_ids


def main():
    token = os.environ["GH_TOKEN"]
    repo = os.environ["REPO"]
    from_ref = os.environ["FROM_REF"]
    to_ref = os.environ.get("TO_REF", os.environ.get("GITHUB_SHA", "HEAD"))
    config_path = os.environ.get(
        "RELEASE_DRAFTER_CONFIG",
        str(Path(__file__).with_name("release-drafter.yml")),
    )

    config = load_release_drafter_config(config_path)
    commit_shas = get_commit_range(from_ref, to_ref)
    prs = fetch_merged_prs(repo, token, from_ref, to_ref, commit_shas)
    changes, pr_ids = build_changes(prs, config)

    template = config["template"]
    changelog = template.replace("$CHANGES", changes).replace("{{CHANGELOG}}", changes)
    print(
        json.dumps(
            {
                "changelog": changelog,
                "pull_requests": ",".join(pr_ids),
            }
        )
    )


if __name__ == "__main__":
    main()

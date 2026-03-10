#!/usr/bin/env python3
import argparse
import json
import re
import urllib.parse
import urllib.request
from urllib.error import HTTPError

import yaml


COLOR_RE = re.compile(r"^[0-9a-fA-F]{6}$")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create or update label metadata from a labeler config."
    )
    parser.add_argument("--config-path", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--github-token", required=True)
    return parser.parse_args()


def _api(method, url, token, payload=None):
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "ci-setup-labels",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8")), resp.headers
    except HTTPError as err:
        body = err.read().decode("utf-8", errors="replace")
        raise SystemExit(f"GitHub API error {err.code} for {method} {url}: {body}")


def iter_repo_labels(repo, token):
    page = 1
    out = {}
    while True:
        url = f"https://api.github.com/repos/{repo}/labels?per_page=100&page={page}"
        labels, _headers = _api("GET", url, token)
        if not labels:
            break
        for label in labels:
            name = label.get("name", "")
            if name:
                out[name.lower()] = label
        page += 1
    return out


def parse_target_labels(config_path):
    with open(config_path, "r", encoding="utf-8") as fh:
        labels_cfg = yaml.safe_load(fh) or {}

    if not isinstance(labels_cfg, dict):
        raise SystemExit("Label configuration must be a mapping.")

    parsed = {}
    skipped = []
    for label_name, rules in labels_cfg.items():
        if not isinstance(rules, list):
            skipped.append(label_name)
            continue

        description = None
        color = None
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            if "description" in rule and isinstance(rule["description"], str):
                description = rule["description"]
            if "color" in rule and isinstance(rule["color"], str):
                color = rule["color"].lstrip("#")

        if color is None or not COLOR_RE.fullmatch(color):
            skipped.append(label_name)
            continue

        parsed[label_name] = {"name": label_name, "color": color.lower()}
        if description is not None:
            parsed[label_name]["description"] = description

    return parsed, skipped


def upsert_labels(repo, token, desired, existing):
    created = []
    updated = []
    unchanged = []

    for label_name in sorted(desired.keys()):
        target = desired[label_name]
        current = existing.get(label_name.lower())
        if current is None:
            url = f"https://api.github.com/repos/{repo}/labels"
            _api("POST", url, token, payload=target)
            created.append(label_name)
            continue

        current_color = str(current.get("color", "")).lower()
        target_color = target["color"].lower()
        current_desc = current.get("description") or ""
        target_desc = target.get("description") or ""

        if current_color == target_color and current_desc == target_desc:
            unchanged.append(label_name)
            continue

        encoded_name = urllib.parse.quote(current["name"], safe="")
        url = f"https://api.github.com/repos/{repo}/labels/{encoded_name}"
        payload = {
            "new_name": label_name,
            "color": target_color,
            "description": target_desc,
        }
        _api("PATCH", url, token, payload=payload)
        updated.append(label_name)

    return created, updated, unchanged


def main():
    args = parse_args()
    desired_labels, skipped_labels = parse_target_labels(args.config_path)
    existing_labels = iter_repo_labels(args.repo, args.github_token)

    created, updated, unchanged = upsert_labels(
        args.repo,
        args.github_token,
        desired_labels,
        existing_labels,
    )

    print(
        json.dumps(
            {
                "created_labels": created,
                "updated_labels": updated,
                "unchanged_labels": unchanged,
                "skipped_labels": sorted(skipped_labels),
            }
        )
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import argparse
import json
import re
import urllib.parse
import urllib.request
from urllib.error import HTTPError, URLError

import yaml


COLOR_RE = re.compile(r"^[0-9a-fA-F]{6}$")
DEFAULT_COLOR = "808080"


class GitHubApiError(RuntimeError):
    pass


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create or update label metadata from a labeler config."
    )
    parser.add_argument("--config-path", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--github-token", required=True)
    parser.add_argument("--output-path", required=True)
    return parser.parse_args()


def api(method, url, token, payload=None):
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
        raise GitHubApiError(f"GitHub API error {err.code} for {method} {url}: {body}")
    except URLError as err:
        raise GitHubApiError(f"GitHub API request failed for {method} {url}: {err}")


def iter_repo_labels(repo, token):
    page = 1
    out = {}
    while True:
        url = f"https://api.github.com/repos/{repo}/labels?per_page=100&page={page}"
        labels, _headers = api("GET", url, token)
        if not labels:
            break
        for label in labels:
            name = label.get("name", "")
            if name:
                out[name.lower()] = label
        page += 1
    return out


def build_label_plan(config_path):
    with open(config_path, "r", encoding="utf-8") as fh:
        labels_cfg = yaml.safe_load(fh) or {}

    if not isinstance(labels_cfg, dict):
        return {}, [], ["Label configuration must be a mapping."]

    planned = {}
    skipped = []
    errors = []
    for label_name, rules in labels_cfg.items():
        if not isinstance(rules, list):
            errors.append(f"{label_name}: rules must be a list")
            continue

        label_errors = []
        description = None
        color = None
        saw_description = False
        saw_color = False
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            if "description" in rule:
                saw_description = True
                if isinstance(rule["description"], str):
                    description = rule["description"]
                else:
                    label_errors.append(f"{label_name}: description must be a string")
            if "color" in rule:
                saw_color = True
                if not isinstance(rule["color"], str):
                    label_errors.append(f"{label_name}: color must be a string")
                    continue
                normalized_color = rule["color"].lstrip("#")
                if COLOR_RE.fullmatch(normalized_color):
                    color = normalized_color.lower()
                else:
                    label_errors.append(
                        f"{label_name}: color must be a six-character hex value"
                    )

        if label_errors:
            errors.extend(label_errors)
            continue
        if not saw_description and not saw_color:
            skipped.append(label_name)
            continue
        if description is None:
            skipped.append(label_name)
            continue

        planned[label_name] = {
            "name": label_name,
            "description": description,
            "color": color or DEFAULT_COLOR,
        }

    return planned, skipped, errors


def apply_labels(repo, token, planned):
    created = []
    updated = []
    unchanged = []
    errors = []

    try:
        existing = iter_repo_labels(repo, token)
    except GitHubApiError as err:
        return created, updated, unchanged, [str(err)]

    for label_name in sorted(planned.keys()):
        target = planned[label_name]
        current = existing.get(label_name.lower())
        if current is None:
            url = f"https://api.github.com/repos/{repo}/labels"
            try:
                api("POST", url, token, payload=target)
            except GitHubApiError as err:
                errors.append(str(err))
                continue
            created.append(label_name)
            continue

        current_color = str(current.get("color", "")).lower()
        current_desc = current.get("description") or ""
        payload = {"new_name": label_name}

        if target["color"] != current_color:
            payload["color"] = target["color"]
        if target["description"] != current_desc:
            payload["description"] = target["description"]

        if payload == {"new_name": label_name}:
            unchanged.append(label_name)
            continue

        encoded_name = urllib.parse.quote(current["name"], safe="")
        url = f"https://api.github.com/repos/{repo}/labels/{encoded_name}"
        try:
            api("PATCH", url, token, payload=payload)
        except GitHubApiError as err:
            errors.append(str(err))
            continue
        updated.append(label_name)

    return created, updated, unchanged, errors


def main():
    args = parse_args()
    planned, skipped, plan_errors = build_label_plan(args.config_path)

    created = []
    updated = []
    unchanged = []
    apply_errors = []
    if not plan_errors:
        created, updated, unchanged, apply_errors = apply_labels(
            args.repo, args.github_token, planned
        )

    result = {
        "created_labels": created,
        "updated_labels": updated,
        "unchanged_labels": unchanged,
        "skipped_labels": sorted(skipped),
        "errors": sorted(plan_errors + apply_errors),
    }

    with open(args.output_path, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2, sort_keys=True)
    print(json.dumps(result))


if __name__ == "__main__":
    main()

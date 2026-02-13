#!/usr/bin/env python3
from pathlib import Path

import yaml


def _as_label_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    return []


def load_release_drafter_config(path):
    raw = Path(path).read_text(encoding="utf-8")
    parsed = yaml.safe_load(raw) or {}

    categories = []
    for category in parsed.get("categories", []) or []:
        if not isinstance(category, dict):
            continue
        title = str(category.get("title", ""))
        labels = []
        labels.extend(_as_label_list(category.get("label")))
        labels.extend(_as_label_list(category.get("labels")))
        categories.append({"title": title, "labels": labels})

    version_resolver = {"major": set(), "minor": set(), "patch": set()}
    resolver_raw = parsed.get("version-resolver", {}) or {}
    if isinstance(resolver_raw, dict):
        for level in ("major", "minor", "patch"):
            level_cfg = resolver_raw.get(level, {}) or {}
            if isinstance(level_cfg, dict):
                version_resolver[level] = set(_as_label_list(level_cfg.get("labels")))

    exclude_labels = set(_as_label_list(parsed.get("exclude-labels")))

    return {
        "name_template": str(parsed.get("name-template", "Release v$RESOLVED_VERSION")),
        "tag_template": str(parsed.get("tag-template", "v$RESOLVED_VERSION")),
        "template": str(parsed.get("template", "# What’s Changed\n\n$CHANGES")),
        "categories": categories,
        "version_resolver": version_resolver,
        "exclude_labels": exclude_labels,
    }

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


def load_changelog_config(path):
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

    exclude_labels = set(_as_label_list(parsed.get("exclude-labels")))

    return {
        "template": str(parsed.get("template", "# What’s Changed\n\n$CHANGES")),
        "categories": categories,
        "exclude_labels": exclude_labels,
    }

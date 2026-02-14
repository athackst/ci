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


def load_version_config(path):
    raw = Path(path).read_text(encoding="utf-8")
    parsed = yaml.safe_load(raw) or {}

    version_resolver = {"major": set(), "minor": set(), "patch": set()}
    resolver_raw = parsed.get("version-resolver", {}) or {}
    if isinstance(resolver_raw, dict):
        for level in ("major", "minor", "patch"):
            level_cfg = resolver_raw.get(level, {}) or {}
            if isinstance(level_cfg, dict):
                version_resolver[level] = set(_as_label_list(level_cfg.get("labels")))

    return {
        "version_resolver": version_resolver,
    }

#!/usr/bin/env python3
"""Layer the action's base Jekyll config under the repository config."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from string import Template

import yaml


def load_yaml(path: Path) -> object:
    """Load YAML from a file, treating missing or empty files as empty dicts."""
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as stream:
        return yaml.safe_load(stream) or {}


def render_yaml_template(path: Path) -> object:
    """Render the action template using environment-backed YAML-safe values."""
    template = Template(path.read_text(encoding="utf-8"))
    rendered = template.substitute(
        title=json.dumps(os.environ["TITLE"]),
        description=json.dumps(os.environ["DESCRIPTION"]),
        image="null" if not os.environ["IMAGE"] else json.dumps(os.environ["IMAGE"]),
        edit_url=json.dumps(os.environ["EDIT_URL"]),
        repository=json.dumps(os.environ["REPOSITORY"]),
        versions="true" if os.environ["VERSIONS_ENABLED"].lower() == "true" else "false",
    )
    return yaml.safe_load(rendered) or {}


def merge_values(base: object, override: object) -> object:
    """Recursively merge dicts, letting override values win."""
    if isinstance(base, dict) and isinstance(override, dict):
        merged = dict(base)
        for key, value in override.items():
            merged[key] = merge_values(merged.get(key), value)
        return merged

    return override


def main() -> int:
    base_path = Path(sys.argv[1])
    local_path = Path(sys.argv[2])

    merged = merge_values(load_yaml(local_path), render_yaml_template(base_path))
    if merged.get("image") is None:
        merged.pop("image", None)

    with local_path.open("w", encoding="utf-8") as stream:
        yaml.safe_dump(merged, stream, sort_keys=False)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

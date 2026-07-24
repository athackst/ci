#!/usr/bin/env python3
"""Render the action's managed Jekyll configuration."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from string import Template

import yaml


def render_yaml_template(path: Path) -> object:
    """Render the action template using environment-backed YAML-safe values."""
    template = Template(path.read_text(encoding="utf-8"))
    rendered = template.substitute(
        title=json.dumps(os.environ["TITLE"]),
        description=json.dumps(os.environ["DESCRIPTION"]),
        image="null" if not os.environ["IMAGE"] else json.dumps(os.environ["IMAGE"]),
        edit_url=json.dumps(os.environ["EDIT_URL"]),
        repository=json.dumps(os.environ["REPOSITORY"]),
        nav_filename=json.dumps(os.environ["NAV_FILENAME"]),
        versions="true" if os.environ["VERSIONS_ENABLED"].lower() == "true" else "false",
        versions_config=json.dumps(os.environ["VERSIONS_CONFIG"]),
        prefix=json.dumps(os.environ["PREFIX"]),
    )
    return yaml.safe_load(rendered) or {}


def main() -> int:
    template_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    rendered = render_yaml_template(template_path)
    if rendered.get("image") is None:
        rendered.pop("image", None)

    with output_path.open("w", encoding="utf-8") as stream:
        yaml.safe_dump(rendered, stream, sort_keys=False)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

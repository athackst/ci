#!/usr/bin/env python3
"""Render the managed Jekyll configuration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from string import Template

import yaml


def render_yaml_template(template_path: Path, values: dict[str, str]) -> dict:
    """Render the Jekyll YAML template using YAML-safe values."""

    template = Template(template_path.read_text(encoding="utf-8"))
    rendered = template.substitute(
        title=json.dumps(values["title"]),
        description=json.dumps(values["description"]),
        image="null" if not values["image"] else json.dumps(values["image"]),
        edit_url=json.dumps(values["edit_url"]),
        repository=json.dumps(values["repository"]),
        versions="true" if values["versions_config"] else "false",
        versions_config=json.dumps(values["versions_config"]),
        prefix=json.dumps(values["base_path"]),
    )
    config = yaml.safe_load(rendered) or {}
    if config.get("image") is None:
        config.pop("image", None)
    return config


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--description", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--edit-url", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--versions-config", required=True)
    parser.add_argument("--base-path", required=True)
    args = parser.parse_args()

    rendered = render_yaml_template(
        args.template,
        {
            "title": args.title,
            "description": args.description,
            "image": args.image,
            "edit_url": args.edit_url,
            "repository": args.repository,
            "versions_config": args.versions_config,
            "base_path": args.base_path,
        },
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as stream:
        yaml.safe_dump(rendered, stream, sort_keys=False)
    print(f"Rendered Jekyll configuration to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

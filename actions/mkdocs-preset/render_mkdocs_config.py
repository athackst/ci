#!/usr/bin/env python3
"""Render the managed MkDocs configuration for a workspace."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from string import Template


def render_yaml_template(template_path: Path, values: dict[str, str]) -> str:
    """Render the MkDocs YAML template using YAML-safe string values."""

    template = Template(template_path.read_text(encoding="utf-8"))
    return template.substitute(
        **{name: json.dumps(value) for name, value in values.items()}
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--docs-dir", required=True)
    parser.add_argument("--site-dir", required=True)
    parser.add_argument("--overrides-dir", required=True)
    parser.add_argument("--site-name", required=True)
    parser.add_argument("--repo-url", required=True)
    parser.add_argument("--site-url", required=True)
    parser.add_argument("--edit-uri", required=True)
    args = parser.parse_args()

    rendered = render_yaml_template(
        args.template,
        {
            "docs_dir": args.docs_dir,
            "site_dir": args.site_dir,
            "overrides_dir": args.overrides_dir,
            "site_name": args.site_name,
            "repo_url": args.repo_url,
            "site_url": args.site_url,
            "edit_uri": args.edit_uri,
        },
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(f"Rendered MkDocs configuration to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

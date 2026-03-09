#!/usr/bin/env python3
import json
import os
import string
from pathlib import Path

import yaml


def main() -> int:
    config_path = os.environ.get("CONFIG_PATH", "")
    version = os.environ.get("VERSION", "")
    resolved_version = os.environ.get("RESOLVED_VERSION", "") or version
    changelog = os.environ.get("CHANGELOG", "")

    if not config_path:
        raise SystemExit("CONFIG_PATH is required.")
    if not (version or resolved_version):
        raise SystemExit("VERSION or RESOLVED_VERSION is required.")

    cfg = yaml.safe_load(Path(config_path).read_text(encoding="utf-8")) or {}
    name_template = str(cfg.get("name-template", "Release v$RESOLVED_VERSION"))
    tag_template = str(cfg.get("tag-template", "v$RESOLVED_VERSION"))
    body_template = str(cfg.get("template", "# What’s Changed\n\n$CHANGES"))

    ctx = {
        "VERSION": version or resolved_version,
        "RESOLVED_VERSION": resolved_version or version,
        "CHANGES": changelog,
        "CHANGELOG": changelog,
    }

    print(
        json.dumps(
            {
                "name": string.Template(name_template).safe_substitute(ctx),
                "tag_name": string.Template(tag_template).safe_substitute(ctx),
                "body": string.Template(body_template).safe_substitute(ctx),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

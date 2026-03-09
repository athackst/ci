#!/usr/bin/env python3
import argparse
import base64
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

import yaml
from jsonschema import ValidationError, validate


def parse_args():
    parser = argparse.ArgumentParser(
        description="Resolve and flatten PR labeler configuration."
    )
    parser.add_argument(
        "--configuration-path",
        default="",
        help="Optional configuration path input.",
    )
    parser.add_argument(
        "--default-configuration-path",
        required=True,
        help="Default bundled configuration path.",
    )
    parser.add_argument(
        "--output-path",
        required=True,
        help="Path to write flattened label config YAML.",
    )
    parser.add_argument(
        "--repo",
        default="",
        help="Repository in owner/repo format used for API fallback fetch.",
    )
    parser.add_argument(
        "--ref",
        default="",
        help="Git ref or SHA used for API fallback fetch.",
    )
    parser.add_argument(
        "--github-token",
        default="",
        help="GitHub token used for API fallback fetch.",
    )
    return parser.parse_args()


def read_config_via_api(path: str, repo: str, ref: str, token: str):
    if not path or not repo or not token:
        return None

    encoded_path = quote(path.lstrip("/"), safe="/")
    url = f"https://api.github.com/repos/{repo}/contents/{encoded_path}"
    if ref:
        url = f"{url}?ref={quote(ref, safe='')}"

    req = Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "ci-pr-labeler",
        },
    )
    try:
        with urlopen(req) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except HTTPError:
        return None

    content = payload.get("content", "")
    encoding = payload.get("encoding", "")
    if encoding != "base64" or not content:
        return None
    return base64.b64decode(content).decode("utf-8")


def load_schema():
    schema_path = Path(__file__).with_name("labeler.schema.json")
    return json.loads(schema_path.read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()

    default_config_path = Path(args.default_configuration_path)
    source_config_path = ""
    config_text = ""

    if args.configuration_path:
        requested_path = Path(args.configuration_path)
        if requested_path.exists():
            source_config_path = str(requested_path)
            config_text = requested_path.read_text(encoding="utf-8")
        else:
            fetched = read_config_via_api(
                path=args.configuration_path,
                repo=args.repo or os.environ.get("GITHUB_REPOSITORY", ""),
                ref=args.ref or os.environ.get("GITHUB_SHA", ""),
                token=args.github_token or os.environ.get("GITHUB_TOKEN", ""),
            )
            if fetched is not None:
                source_config_path = (
                    f"{args.repo or os.environ.get('GITHUB_REPOSITORY', '')}"
                    f"@{args.ref or os.environ.get('GITHUB_SHA', '')}:{args.configuration_path}"
                )
                config_text = fetched
            else:
                if not default_config_path.exists():
                    raise SystemExit(
                        "Config not found locally, API fetch failed, and default config missing."
                    )
                source_config_path = str(default_config_path)
                config_text = default_config_path.read_text(encoding="utf-8")
    else:
        if not default_config_path.exists():
            raise SystemExit(f"Config not found: {default_config_path}")
        source_config_path = str(default_config_path)
        config_text = default_config_path.read_text(encoding="utf-8")

    data = yaml.safe_load(config_text) or {}
    labels = data.get("labels")
    if not isinstance(labels, dict):
        labels = data
    try:
        validate(instance=labels, schema=load_schema())
    except ValidationError as err:
        location = ".".join(str(p) for p in err.absolute_path) or "<root>"
        raise SystemExit(f"Labeler config schema validation failed at {location}: {err.message}")

    output_path = Path(args.output_path)
    output_path.write_text(
        yaml.safe_dump(labels, sort_keys=False),
        encoding="utf-8",
    )

    print(f"source-config-path={source_config_path}")
    print(f"config-path={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

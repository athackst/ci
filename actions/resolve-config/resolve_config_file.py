#!/usr/bin/env python3
import argparse
import base64
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen


def parse_args():
    parser = argparse.ArgumentParser(
        description="Resolve config file from local path or GitHub API."
    )
    parser.add_argument(
        "--configuration-path",
        required=True,
        help="Configuration path input.",
    )
    parser.add_argument(
        "--output-path",
        required=True,
        help="Path to write resolved config file.",
    )
    parser.add_argument(
        "--repo",
        default="",
        help="Repository in owner/repo format used for API fetch.",
    )
    parser.add_argument(
        "--ref",
        default="",
        help="Git ref or SHA used for API fetch.",
    )
    parser.add_argument(
        "--github-token",
        default="",
        help="GitHub token used for API fetch.",
    )
    return parser.parse_args()


def read_via_api(path: str, repo: str, ref: str, token: str):
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
            "User-Agent": "ci-shared-config-resolver",
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


def main() -> int:
    args = parse_args()

    repo = args.repo or os.environ.get("GITHUB_REPOSITORY", "")
    ref = args.ref or os.environ.get("GITHUB_SHA", "")
    token = args.github_token or os.environ.get("GITHUB_TOKEN", "")

    source_config_path = ""
    resolved_text = ""
    requested_path = Path(args.configuration_path)
    if requested_path.exists():
        source_config_path = str(requested_path)
        resolved_text = requested_path.read_text(encoding="utf-8")
    else:
        fetched = read_via_api(args.configuration_path, repo, ref, token)
        if fetched is None:
            raise SystemExit(
                f"Config not found locally and API fetch failed: {args.configuration_path}"
            )
        source_config_path = f"{repo}@{ref}:{args.configuration_path}"
        resolved_text = fetched

    output_path = Path(args.output_path)
    output_path.write_text(resolved_text, encoding="utf-8")

    print(f"source-config-path={source_config_path}")
    print(f"config-path={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

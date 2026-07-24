#!/usr/bin/env python3
"""Resolve and normalize a site's location settings."""

from __future__ import annotations

import argparse
import json
from urllib.parse import urlsplit, urlunsplit


def normalize_origin(value: str) -> tuple[str, str]:
    candidate = value.strip().rstrip("/")
    if not candidate:
        raise ValueError("host must not be empty")
    if "://" not in candidate:
        candidate = f"https://{candidate}"

    parsed = urlsplit(candidate)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("host scheme must be http or https")
    if not parsed.netloc:
        raise ValueError("host must include a domain")
    if parsed.username or parsed.password:
        raise ValueError("host must not include credentials")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise ValueError("host must not include a path, query, or fragment")

    return urlunsplit((parsed.scheme, parsed.netloc, "", "", "")), parsed.netloc


def normalize_path(value: str, *, name: str) -> str:
    candidate = value.strip()
    if not candidate or candidate == "/":
        return ""
    if "?" in candidate or "#" in candidate:
        raise ValueError(f"{name} must not include a query or fragment")
    return f"/{candidate.strip('/')}"


def resolve_site_settings(
    *,
    host: str,
    base_path: str = "",
    base_url: str = "",
    version: str = "",
) -> dict[str, str]:
    origin, normalized_host = normalize_origin(host)
    normalized_base_path = normalize_path(base_path, name="base-path")

    if base_url.strip():
        candidate = base_url.strip().rstrip("/")
        if "://" not in candidate:
            candidate = f"https://{candidate}"
        parsed = urlsplit(candidate)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("base-url must be an http or https URL")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError(
                "base-url must not include credentials, a query, or a fragment"
            )

        base_origin = urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
        if base_origin != origin:
            raise ValueError("base-url origin must match host")

        url_path = normalize_path(parsed.path, name="base-url path")
        if normalized_base_path and url_path != normalized_base_path:
            raise ValueError("base-url path must match base-path")
        normalized_base_path = normalized_base_path or url_path

    return {
        "host": normalized_host,
        "base_path": normalized_base_path,
        "base_url": f"{origin}{normalized_base_path}",
        "version": normalize_path(version, name="version").lstrip("/"),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True)
    parser.add_argument("--base-path", default="")
    parser.add_argument("--base-url", default="")
    parser.add_argument("--version", default="")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        settings = resolve_site_settings(
            host=args.host,
            base_path=args.base_path,
            base_url=args.base_url,
            version=args.version,
        )
    except ValueError as error:
        raise SystemExit(f"Invalid site settings: {error}") from error

    print(json.dumps(settings, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

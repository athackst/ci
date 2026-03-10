#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import yaml
from jsonschema import ValidationError, validate


def parse_args():
    parser = argparse.ArgumentParser(
        description="Extract and validate PR labeler labels configuration."
    )
    parser.add_argument(
        "--config-path",
        required=True,
        help="Path to config YAML.",
    )

    parser.add_argument(
        "--output-path",
        required=True,
        help="Path to write flattened label config YAML.",
    )
    return parser.parse_args()


def load_schema():
    schema_path = Path(__file__).with_name("labeler.schema.json")
    return json.loads(schema_path.read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()

    config_path = Path(args.config_path)
    if not config_path.exists():
        raise SystemExit(f"Config not found: {config_path}")

    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    labels = data.get("labels")
    if not isinstance(labels, dict):
        labels = data

    try:
        validate(instance=labels, schema=load_schema())
    except ValidationError as err:
        location = ".".join(str(p) for p in err.absolute_path) or "<root>"
        raise SystemExit(
            f"Labeler config schema validation failed at {location}: {err.message}"
        )

    output_path = Path(args.output_path)
    output_path.write_text(
        yaml.safe_dump(labels, sort_keys=False),
        encoding="utf-8",
    )

    print(f"config-path={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

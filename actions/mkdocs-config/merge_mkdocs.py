#!/usr/bin/env python3
"""Layer the action's base MkDocs config under the repository config."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml


class TaggedValue:
    """Store a tagged YAML value without resolving the tag to a Python object."""

    def __init__(self, value: object, tag: str) -> None:
        self.value = value
        self.tag = tag


class MkdocsConfigLoader(yaml.SafeLoader):
    """YAML loader that preserves unknown tags used in MkDocs configs."""


class MkdocsConfigDumper(yaml.SafeDumper):
    """YAML dumper that round-trips preserved unknown tags."""


def _construct_tagged_value(
    loader: MkdocsConfigLoader,
    tag_suffix: str,
    node: yaml.Node,
) -> TaggedValue:
    tag = node.tag
    if isinstance(node, yaml.ScalarNode):
        value: object = loader.construct_scalar(node)
    elif isinstance(node, yaml.SequenceNode):
        value = loader.construct_sequence(node)
    else:
        value = loader.construct_mapping(node)
    return TaggedValue(value=value, tag=tag)


def _represent_tagged_value(
    dumper: MkdocsConfigDumper,
    data: TaggedValue,
) -> yaml.Node:
    if isinstance(data.value, list):
        return dumper.represent_sequence(data.tag, data.value)
    if isinstance(data.value, dict):
        return dumper.represent_mapping(data.tag, data.value)
    return dumper.represent_scalar(data.tag, "" if data.value is None else str(data.value))


MkdocsConfigLoader.add_multi_constructor("", _construct_tagged_value)
MkdocsConfigDumper.add_representer(TaggedValue, _represent_tagged_value)


def load_yaml(path: Path) -> object:
    """Load YAML from a file, treating missing or empty files as empty dicts."""
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as stream:
        return yaml.load(stream, Loader=MkdocsConfigLoader) or {}


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

    merged = merge_values(load_yaml(base_path), load_yaml(local_path))

    with local_path.open("w", encoding="utf-8") as stream:
        yaml.dump(merged, stream, sort_keys=False, Dumper=MkdocsConfigDumper)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

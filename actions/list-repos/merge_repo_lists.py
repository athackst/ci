#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def main() -> int:
    repositories_by_name: dict[str, dict[str, Any]] = {}
    for path_arg in sys.argv[1:]:
        for repository in json.loads(Path(path_arg).read_text()):
            full_name = repository["full_name"]
            repositories_by_name[full_name] = repository

    repositories = sorted(
        repositories_by_name.values(),
        key=lambda repository: repository["full_name"].lower(),
    )
    print(json.dumps(repositories, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

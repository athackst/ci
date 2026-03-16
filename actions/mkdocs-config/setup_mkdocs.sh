#!/bin/bash
set -euo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
python3 "${DIR}/merge_mkdocs.py" "${DIR}/mkdocs.yml" "./mkdocs.yml"
cp -r "${DIR}/overrides" .
touch requirements.txt
cat "${DIR}/requirements.txt" >> requirements.txt

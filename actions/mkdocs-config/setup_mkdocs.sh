#!/bin/bash
set -euo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cp "${DIR}/mkdocs.yml" .
cp -r "${DIR}/overrides" .
touch requirements.txt
cat "${DIR}/requirements.txt" >> requirements.txt

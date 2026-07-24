#!/bin/bash
set -euo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
OUTPUT_DIRECTORY="${OUTPUT_DIRECTORY:-.}"

mkdir -p "$OUTPUT_DIRECTORY"
cp "${DIR}/mkdocs.yml" "$OUTPUT_DIRECTORY/mkdocs.yml"
cp "${DIR}/requirements.txt" "$OUTPUT_DIRECTORY/requirements.txt"
rm -rf "$OUTPUT_DIRECTORY/overrides"
cp -R "${DIR}/overrides" "$OUTPUT_DIRECTORY/overrides"

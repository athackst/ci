#!/bin/bash
set -euo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
OUTPUT_DIRECTORY="${OUTPUT_DIRECTORY:-.}"

mkdir -p "$OUTPUT_DIRECTORY"

python3 "${DIR}/render_jekyll_config.py" \
    "${DIR}/_config.yml" \
    "$OUTPUT_DIRECTORY/_config.yml"
cp "${DIR}/Gemfile" "$OUTPUT_DIRECTORY/Gemfile"
rm -f "$OUTPUT_DIRECTORY/Gemfile.lock"
cp "${DIR}/semiliterate.yml" "$OUTPUT_DIRECTORY/semiliterate.yml"

echo "Created managed Jekyll files in $OUTPUT_DIRECTORY."

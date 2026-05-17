#!/bin/bash
set -euo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

if [[ ! -f "./_config.yml" ]]; then
    python3 "${DIR}/merge_jekyll_config.py" "${DIR}/_config.yml" "./_config.yml"
    echo "Created _config.yml from template."
fi

if [[ ! -f "./Gemfile" ]]; then
    cp "${DIR}/Gemfile" "./Gemfile"
    echo "Created Gemfile from template."
fi

if [[ ! -f "./semiliterate.yml" ]]; then
    cp "${DIR}/semiliterate.yml" "./semiliterate.yml"
    echo "Created semiliterate.yml from template."
fi

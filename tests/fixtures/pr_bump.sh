#!/usr/bin/env bash
set -euo pipefail

OUT_FILE="tests/fixtures/pr_bump_output.txt"

mkdir -p "$(dirname "$OUT_FILE")"

cat > "$OUT_FILE" <<EOF
run_id=${GITHUB_RUN_ID:-}
run_attempt=${GITHUB_RUN_ATTEMPT:-}
from_ref=${FROM_REF:-}
resolved_version=${RESOLVED_VERSION:-}
major_version=${MAJOR_VERSION:-}
minor_version=${MINOR_VERSION:-}
patch_version=${PATCH_VERSION:-}
version_parts=${MAJOR_VERSION:-}.${MINOR_VERSION:-}.${PATCH_VERSION:-}
pr_info_path=${PR_INFO_PATH:-}
EOF


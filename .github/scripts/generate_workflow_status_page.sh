#!/usr/bin/env bash
set -euo pipefail

if [ -z "${GH_TOKEN:-}" ]; then
  export GH_TOKEN="$(gh auth token)"
fi

SOURCES=("$@")
if [ "${#SOURCES[@]}" -eq 0 ]; then
  mapfile -t SOURCES <<< "${REPOSITORY_SOURCES:-}"
fi
if [ "${#SOURCES[@]}" -eq 0 ]; then
  echo "No repository sources configured."
  exit 1
fi

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
for index in "${!SOURCES[@]}"; do
  source="${SOURCES[$index]}"
  source="${source#"${source%%[![:space:]]*}"}"
  source="${source%"${source##*[![:space:]]}"}"
  if [ -z "$source" ]; then
    continue
  fi
  if [[ ! "$source" =~ ^[A-Za-z0-9_.-]+$ ]]; then
    echo "Invalid repository owner: $source"
    exit 1
  fi

  echo "Listing managed repositories for $source"
  python3 .github/scripts/list_repos.py \
    --debug-timing \
    --user "$source" \
    --fork false \
    --archived false \
    --private false \
    --filter-path .copier-answers.ci.yml > "$TMP_DIR/source-${index}.json"
done

if ! compgen -G "$TMP_DIR/*.json" > /dev/null; then
  echo "No repository sources configured."
  exit 1
fi

jq -s '
  add
  | unique_by(.full_name)
  | sort_by(.full_name | ascii_downcase)
' "$TMP_DIR"/*.json > "$TMP_DIR/repositories.json"

python3 .github/scripts/generate_workflow_status.py \
  --repos-file "$TMP_DIR/repositories.json"

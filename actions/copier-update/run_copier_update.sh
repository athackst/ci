#!/usr/bin/env bash

set -euo pipefail

ANSWERS_FILE=""
VCS_REF=""
RESULT_FILE=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --answers-file)
      ANSWERS_FILE="$2"
      shift 2
      ;;
    --vcs-ref)
      VCS_REF="$2"
      shift 2
      ;;
    --result-file)
      RESULT_FILE="$2"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [ -z "$ANSWERS_FILE" ] || [ -z "$RESULT_FILE" ]; then
  echo "--answers-file and --result-file are required." >&2
  exit 2
fi

json_array() {
  if [ "$#" -eq 0 ]; then
    printf '[]'
    return
  fi

  printf '%s\n' "$@" | jq --raw-input . | jq --slurp .
}

write_result() {
  local answers_found="$1"
  local command="$2"
  local changed_files_json="$3"
  local conflicted_files_json="$4"

  jq --null-input \
    --argjson answers_found "$answers_found" \
    --arg command "$command" \
    --argjson changed_files "$changed_files_json" \
    --argjson conflicted_files "$conflicted_files_json" \
    '{
      answers_found: $answers_found,
      command: $command,
      changed: ($changed_files | length > 0),
      changed_files: $changed_files,
      conflicts_found: ($conflicted_files | length > 0),
      conflicted_files: $conflicted_files
    }' > "$RESULT_FILE"
}

if [ ! -f "$ANSWERS_FILE" ]; then
  write_result false "" '[]' '[]'
  echo "Required Copier answers file not found: $ANSWERS_FILE"
  exit 1
fi

copier_args=(update --trust -a "$ANSWERS_FILE" -A --defaults)
if [ -n "$VCS_REF" ]; then
  copier_args+=(--vcs-ref "$VCS_REF")
fi

printf -v COPIER_COMMAND '%q ' copier "${copier_args[@]}"
COPIER_COMMAND="${COPIER_COMMAND% }"
write_result true "$COPIER_COMMAND" '[]' '[]'

echo "Running: $COPIER_COMMAND"
set +e
copier "${copier_args[@]}"
UPDATE_STATUS=$?
set -e

CHANGED_FILES=()
while IFS= read -r -d '' entry; do
  status="${entry:0:2}"
  CHANGED_FILES+=("${entry:3}")

  if [[ "$status" == *R* || "$status" == *C* ]]; then
    IFS= read -r -d '' original_path || true
  fi
done < <(git status --porcelain=v1 -z)

CONFLICT_OUTPUT="$(git diff --name-only --diff-filter=U)"
CONFLICTED_FILES=()
while IFS= read -r line; do
  if [ -n "$line" ]; then
    CONFLICTED_FILES+=("$line")
  fi
done <<< "$CONFLICT_OUTPUT"

CHANGED_FILES_JSON="$(json_array "${CHANGED_FILES[@]}")"
CONFLICTED_FILES_JSON="$(json_array "${CONFLICTED_FILES[@]}")"
write_result true "$COPIER_COMMAND" "$CHANGED_FILES_JSON" "$CONFLICTED_FILES_JSON"

if [ "${#CHANGED_FILES[@]}" -gt 0 ]; then
  echo "Copier produced changes:"
  printf '%s\n' "${CHANGED_FILES[@]}"
else
  echo "Copier produced no changes."
fi

if [ "${#CONFLICTED_FILES[@]}" -gt 0 ]; then
  echo "Copier produced merge conflicts:"
  printf '%s\n' "${CONFLICTED_FILES[@]}"
  exit 1
fi

exit "$UPDATE_STATUS"

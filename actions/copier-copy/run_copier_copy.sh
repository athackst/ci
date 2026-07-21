#!/usr/bin/env bash

set -euo pipefail

SOURCE=""
DESTINATION=""
ANSWERS_FILE=""
VCS_REF=""
OVERWRITE="true"
RESULT_FILE=""

while [ "$#" -gt 0 ]; do
  case "$1" in
    --source)
      SOURCE="$2"
      shift 2
      ;;
    --destination)
      DESTINATION="$2"
      shift 2
      ;;
    --answers-file)
      ANSWERS_FILE="$2"
      shift 2
      ;;
    --vcs-ref)
      VCS_REF="$2"
      shift 2
      ;;
    --overwrite)
      OVERWRITE="$2"
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

if [ -z "$SOURCE" ] || [ -z "$DESTINATION" ] || [ -z "$RESULT_FILE" ]; then
  echo "--source, --destination, and --result-file are required." >&2
  exit 2
fi

if [ "$OVERWRITE" != "true" ] && [ "$OVERWRITE" != "false" ]; then
  echo "--overwrite must be true or false." >&2
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
  local command="$1"
  local changed_files_json="$2"

  jq --null-input \
    --arg command "$command" \
    --argjson changed_files "$changed_files_json" \
    '{
      command: $command,
      changed: ($changed_files | length > 0),
      changed_files: $changed_files
    }' > "$RESULT_FILE"
}

copier_args=(copy --trust --defaults)
if [ "$OVERWRITE" = "true" ]; then
  copier_args+=(--overwrite)
fi
if [ -n "$ANSWERS_FILE" ]; then
  copier_args+=(--answers-file "$ANSWERS_FILE")
fi
if [ -n "$VCS_REF" ]; then
  copier_args+=(--vcs-ref "$VCS_REF")
fi
copier_args+=("$SOURCE" "$DESTINATION")

printf -v COPIER_COMMAND '%q ' copier "${copier_args[@]}"
COPIER_COMMAND="${COPIER_COMMAND% }"
write_result "$COPIER_COMMAND" '[]'

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Copier Copy requires a checked-out Git worktree to detect changes." >&2
  exit 1
fi

if [ -n "$(git status --porcelain=v1)" ]; then
  echo "Destination repository is dirty; commit or stash existing changes before running Copier Copy." >&2
  exit 1
fi

echo "Running: $COPIER_COMMAND"
set +e
copier "${copier_args[@]}"
COPY_STATUS=$?
set -e

CHANGED_FILES=()
while IFS= read -r -d '' entry; do
  status="${entry:0:2}"
  CHANGED_FILES+=("${entry:3}")

  if [[ "$status" == *R* || "$status" == *C* ]]; then
    IFS= read -r -d '' original_path || true
  fi
done < <(git status --porcelain=v1 -z --untracked-files=all)

CHANGED_FILES_JSON="$(json_array "${CHANGED_FILES[@]}")"
write_result "$COPIER_COMMAND" "$CHANGED_FILES_JSON"

if [ "${#CHANGED_FILES[@]}" -gt 0 ]; then
  echo "Copier produced changes:"
  printf '%s\n' "${CHANGED_FILES[@]}"
else
  echo "Copier produced no changes."
fi

exit "$COPY_STATUS"

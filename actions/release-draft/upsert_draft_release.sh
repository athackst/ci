#!/usr/bin/env bash
set -euo pipefail

if [ -z "${TAG_NAME:-}" ]; then
  echo "TAG_NAME is required." >&2
  exit 1
fi
if [ -z "${RELEASE_NAME:-}" ]; then
  echo "RELEASE_NAME is required." >&2
  exit 1
fi

PAYLOAD_FILE="$(mktemp)"
ERROR_FILE="$(mktemp)"
trap 'rm -f "$PAYLOAD_FILE" "$ERROR_FILE"' EXIT

jq -n \
  --arg tag_name "$TAG_NAME" \
  --arg name "$RELEASE_NAME" \
  --arg body "${CHANGELOG:-}" \
  '{tag_name: $tag_name, name: $name, body: $body, draft: true, prerelease: false}' > "$PAYLOAD_FILE"

if [ -n "${DRAFT_RELEASE_ID:-}" ]; then
  if RELEASE_JSON="$(
    gh api -X PATCH "repos/${GITHUB_REPOSITORY}/releases/${DRAFT_RELEASE_ID}" --input "$PAYLOAD_FILE" 2>"$ERROR_FILE"
  )"; then
    printf '%s\n' "$RELEASE_JSON"
    exit 0
  fi
  echo "Unable to update draft release id '${DRAFT_RELEASE_ID}', creating a new draft release." >&2
  cat "$ERROR_FILE" >&2 || true
fi

gh api -X POST "repos/${GITHUB_REPOSITORY}/releases" --input "$PAYLOAD_FILE"

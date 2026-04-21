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
RELEASES_FILE="$(mktemp)"
trap 'rm -f "$PAYLOAD_FILE" "$ERROR_FILE" "$RELEASES_FILE"' EXIT

jq -n \
  --arg tag_name "$TAG_NAME" \
  --arg name "$RELEASE_NAME" \
  --arg body "${CHANGELOG:-}" \
  '{tag_name: $tag_name, name: $name, body: $body, draft: true, prerelease: false}' > "$PAYLOAD_FILE"

patch_release() {
  local release_id="$1"
  gh api -X PATCH "repos/${GITHUB_REPOSITORY}/releases/${release_id}" --input "$PAYLOAD_FILE"
}

load_releases() {
  if [ ! -s "$RELEASES_FILE" ]; then
    gh api "repos/${GITHUB_REPOSITORY}/releases?per_page=100" > "$RELEASES_FILE"
  fi
}

find_draft_release_id_for_tag() {
  load_releases
  jq -r --arg tag_name "$TAG_NAME" '
    map(select(.draft == true and .tag_name == $tag_name))
    | sort_by(.created_at)
    | reverse
    | .[0].id // ""
  ' "$RELEASES_FILE"
}

find_existing_draft_release_id() {
  load_releases
  jq -r '
    map(select(.draft == true))
    | sort_by(.created_at)
    | reverse
    | .[0].id // ""
  ' "$RELEASES_FILE"
}

try_patch_release() {
  local release_id="$1"
  local description="$2"
  if RELEASE_JSON="$(
    patch_release "$release_id" 2>"$ERROR_FILE"
  )"; then
    printf '%s\n' "$RELEASE_JSON"
    exit 0
  fi

  echo "Unable to update ${description} '${release_id}'." >&2
  cat "$ERROR_FILE" >&2 || true
}

if [ -n "${DRAFT_RELEASE_ID:-}" ]; then
  try_patch_release "$DRAFT_RELEASE_ID" "draft release id"
fi

MATCHING_DRAFT_RELEASE_ID="$(find_draft_release_id_for_tag)"
if [ -n "$MATCHING_DRAFT_RELEASE_ID" ]; then
  try_patch_release "$MATCHING_DRAFT_RELEASE_ID" "draft release for tag '${TAG_NAME}'"
fi

if [ "${REUSE_EXISTING_DRAFT:-true}" = "true" ]; then
  EXISTING_DRAFT_RELEASE_ID="$(find_existing_draft_release_id)"
  if [ -n "$EXISTING_DRAFT_RELEASE_ID" ]; then
    try_patch_release "$EXISTING_DRAFT_RELEASE_ID" "existing draft release"
  fi
fi

gh api -X POST "repos/${GITHUB_REPOSITORY}/releases" --input "$PAYLOAD_FILE"

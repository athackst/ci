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

ALL_RELEASES_JSON="$(
  gh api --paginate "repos/${GITHUB_REPOSITORY}/releases?per_page=100"
)"

EXISTING_RELEASE_JSON="$(
  jq -c 'map(select(.draft == true)) | first // empty' <<< "$ALL_RELEASES_JSON"
)"

PAYLOAD_FILE="$(mktemp)"
trap 'rm -f "$PAYLOAD_FILE"' EXIT

if [ -n "$EXISTING_RELEASE_JSON" ]; then
  DRAFT_STATE="$(jq -r '.draft' <<< "$EXISTING_RELEASE_JSON")"
  RELEASE_ID="$(jq -r '.id' <<< "$EXISTING_RELEASE_JSON")"
  if [ "$DRAFT_STATE" != "true" ]; then
    echo "Release ${TAG_NAME} already exists and is not a draft." >&2
    exit 1
  fi

  jq -n \
    --arg tag_name "$TAG_NAME" \
    --arg name "$RELEASE_NAME" \
    --arg body "${CHANGELOG:-}" \
    '{tag_name: $tag_name, name: $name, body: $body, draft: true, prerelease: false}' > "$PAYLOAD_FILE"
  gh api -X PATCH "repos/${GITHUB_REPOSITORY}/releases/${RELEASE_ID}" --input "$PAYLOAD_FILE"
else
  jq -n \
    --arg tag_name "$TAG_NAME" \
    --arg name "$RELEASE_NAME" \
    --arg body "${CHANGELOG:-}" \
    '{tag_name: $tag_name, name: $name, body: $body, draft: true, prerelease: false}' > "$PAYLOAD_FILE"
  gh api -X POST "repos/${GITHUB_REPOSITORY}/releases" --input "$PAYLOAD_FILE"
fi

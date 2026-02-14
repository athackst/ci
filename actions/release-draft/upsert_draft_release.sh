#!/usr/bin/env bash
set -euo pipefail

EXISTING_RELEASE_JSON="$(
  gh api --paginate "repos/${GITHUB_REPOSITORY}/releases?per_page=100" |
    jq -c --arg tag "$TAG_NAME" 'map(select(.tag_name == $tag)) | first // empty'
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
    --arg name "$RELEASE_NAME" \
    --arg body "$CHANGELOG" \
    '{name: $name, body: $body, draft: true}' > "$PAYLOAD_FILE"
  gh api -X PATCH "repos/${GITHUB_REPOSITORY}/releases/${RELEASE_ID}" --input "$PAYLOAD_FILE"
else
  jq -n \
    --arg tag_name "$TAG_NAME" \
    --arg name "$RELEASE_NAME" \
    --arg body "$CHANGELOG" \
    '{tag_name: $tag_name, name: $name, body: $body, draft: true, prerelease: false}' > "$PAYLOAD_FILE"
  gh api -X POST "repos/${GITHUB_REPOSITORY}/releases" --input "$PAYLOAD_FILE"
fi

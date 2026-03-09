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
if [ -z "${RELEASE_MATCH_PATTERN:-}" ]; then
  echo "RELEASE_MATCH_PATTERN is required." >&2
  exit 1
fi

ALL_RELEASES_JSON="$(
  gh api --paginate "repos/${GITHUB_REPOSITORY}/releases?per_page=100"
)"

MATCHING_DRAFTS_JSON="$(
  jq -c --arg pattern "$RELEASE_MATCH_PATTERN" \
    '[.[] | select(.draft == true and ((.tag_name // "") | test($pattern)))]' \
    <<< "$ALL_RELEASES_JSON"
)"
MATCH_COUNT="$(jq 'length' <<< "$MATCHING_DRAFTS_JSON")"

if [ "$MATCH_COUNT" -gt 1 ]; then
  echo "Multiple draft releases matched pattern '$RELEASE_MATCH_PATTERN'." >&2
  jq -r '.[].tag_name' <<< "$MATCHING_DRAFTS_JSON" | sed 's/^/ - /' >&2
  exit 1
fi

EXISTING_RELEASE_JSON="$(
  jq -c 'first // empty' <<< "$MATCHING_DRAFTS_JSON"
)"

PAYLOAD_FILE="$(mktemp)"
trap 'rm -f "$PAYLOAD_FILE"' EXIT

if [ -n "$EXISTING_RELEASE_JSON" ]; then
  RELEASE_ID="$(jq -r '.id' <<< "$EXISTING_RELEASE_JSON")"

  jq -n \
    --arg tag_name "$TAG_NAME" \
    --arg name "$RELEASE_NAME" \
    --arg body "${CHANGELOG:-}" \
    '{tag_name: $tag_name, name: $name, body: $body, draft: true, prerelease: false}' > "$PAYLOAD_FILE"
  gh api -X PATCH "repos/${GITHUB_REPOSITORY}/releases/${RELEASE_ID}" --input "$PAYLOAD_FILE"
else
  RELEASE_WITH_SAME_TAG_EXISTS="$(
    jq -r --arg tag_name "$TAG_NAME" \
      'any(.[]; (.tag_name == $tag_name) and (.draft != true))' \
      <<< "$ALL_RELEASES_JSON"
  )"
  if [ "$RELEASE_WITH_SAME_TAG_EXISTS" = "true" ]; then
    echo "Release ${TAG_NAME} already exists and is not a draft." >&2
    exit 1
  fi

  jq -n \
    --arg tag_name "$TAG_NAME" \
    --arg name "$RELEASE_NAME" \
    --arg body "${CHANGELOG:-}" \
    '{tag_name: $tag_name, name: $name, body: $body, draft: true, prerelease: false}' > "$PAYLOAD_FILE"
  gh api -X POST "repos/${GITHUB_REPOSITORY}/releases" --input "$PAYLOAD_FILE"
fi

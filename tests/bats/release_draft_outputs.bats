#!/usr/bin/env bats

setup() {
  [ -n "${RELEASE_ID:-}" ] || { echo "RELEASE_ID is required" >&2; return 1; }
  [ -n "${RELEASE_NAME:-}" ] || { echo "RELEASE_NAME is required" >&2; return 1; }
  [ -n "${RELEASE_TAG_NAME:-}" ] || { echo "RELEASE_TAG_NAME is required" >&2; return 1; }
  [ -n "${RELEASE_HTML_URL:-}" ] || { echo "RELEASE_HTML_URL is required" >&2; return 1; }
  [ -n "${RELEASE_UPLOAD_URL:-}" ] || { echo "RELEASE_UPLOAD_URL is required" >&2; return 1; }
  [ -n "${EXPECTED_RELEASE_NAME:-}" ] || { echo "EXPECTED_RELEASE_NAME is required" >&2; return 1; }
  [ -n "${EXPECTED_RELEASE_TAG_NAME:-}" ] || { echo "EXPECTED_RELEASE_TAG_NAME is required" >&2; return 1; }
}

@test "release id is numeric" {
  run grep -Eq '^[0-9]+$' <<< "$RELEASE_ID"
  [ "$status" -eq 0 ]
}

@test "release name and tag match expected values" {
  [ "$RELEASE_NAME" = "$EXPECTED_RELEASE_NAME" ]
  [ "$RELEASE_TAG_NAME" = "$EXPECTED_RELEASE_TAG_NAME" ]
}

@test "release urls look valid" {
  [[ "$RELEASE_HTML_URL" == https://github.com/*/releases/tag/* ]]
  [[ "$RELEASE_UPLOAD_URL" == https://uploads.github.com/repos/*/releases/*/assets* ]]
}

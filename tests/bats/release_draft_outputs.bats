#!/usr/bin/env bats

setup() {
  [ -n "${RELEASE_ID:-}" ] || { echo "RELEASE_ID is required" >&2; return 1; }
  [ -n "${RELEASE_NAME:-}" ] || { echo "RELEASE_NAME is required" >&2; return 1; }
  [ -n "${TAG_NAME:-}" ] || { echo "TAG_NAME is required" >&2; return 1; }
  [ -n "${HTML_URL:-}" ] || { echo "HTML_URL is required" >&2; return 1; }
  [ -n "${UPLOAD_URL:-}" ] || { echo "UPLOAD_URL is required" >&2; return 1; }
  [ -n "${RESOLVED_VERSION:-}" ] || { echo "RESOLVED_VERSION is required" >&2; return 1; }
  [ -n "${MARKER:-}" ] || { echo "MARKER is required" >&2; return 1; }
}

@test "release-draft outputs are present and valid" {
  [[ "$RELEASE_ID" =~ ^[0-9]+$ ]]
  [ "$TAG_NAME" = "$MARKER" ]
  [ "$RELEASE_NAME" = "test-release-$MARKER" ]
  [[ "$HTML_URL" =~ ^https://github\.com/.+/releases/tag/.+$ ]]
  [[ "$UPLOAD_URL" =~ ^https://uploads\.github\.com/.+$ ]]
  [[ "$RESOLVED_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]
}

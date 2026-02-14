#!/usr/bin/env bats

setup() {
  [ -n "${FROM_REF:-}" ] || { echo "FROM_REF is required" >&2; return 1; }
  [ -n "${RESOLVED_VERSION:-}" ] || { echo "RESOLVED_VERSION is required" >&2; return 1; }
  [ -n "${MAJOR_VERSION:-}" ] || { echo "MAJOR_VERSION is required" >&2; return 1; }
  [ -n "${MINOR_VERSION:-}" ] || { echo "MINOR_VERSION is required" >&2; return 1; }
  [ -n "${PATCH_VERSION:-}" ] || { echo "PATCH_VERSION is required" >&2; return 1; }
  [ -n "${PR_INFO_PATH:-}" ] || { echo "PR_INFO_PATH is required" >&2; return 1; }
}

@test "resolved version matches major.minor.patch outputs" {
  expected="${MAJOR_VERSION}.${MINOR_VERSION}.${PATCH_VERSION}"
  [ "$expected" = "$RESOLVED_VERSION" ]
}

@test "resolver data json exists and matches resolved version" {
  [ -f "$PR_INFO_PATH" ]
  run jq -r '.resolved_version' "$PR_INFO_PATH"
  [ "$status" -eq 0 ]
  [ "$output" = "$RESOLVED_VERSION" ]
}

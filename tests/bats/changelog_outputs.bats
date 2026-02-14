#!/usr/bin/env bats

setup() {
  [ -n "${CHANGELOG:-}" ] || { echo "CHANGELOG is required" >&2; return 1; }
  [ -n "${PR_INFO_PATH:-}" ] || { echo "PR_INFO_PATH is required" >&2; return 1; }
}

@test "changelog output has expected heading text" {
  [[ "$CHANGELOG" == *"What"* ]]
}

@test "pull requests output is csv of integers when present" {
  if [ -z "${PULL_REQUESTS:-}" ]; then
    skip "No pull requests included."
  fi

  run grep -Eq '^[0-9]+(,[0-9]+)*$' <<< "$PULL_REQUESTS"
  [ "$status" -eq 0 ]
}

@test "pr info file exists and contains pull request array" {
  [ -f "$PR_INFO_PATH" ]
  run jq -r 'if (.pr_info.pull_requests | type) == "array" then "ok" else "bad" end' "$PR_INFO_PATH"
  [ "$status" -eq 0 ]
  [ "$output" = "ok" ]
}

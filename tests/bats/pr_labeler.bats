#!/usr/bin/env bats

setup() {
  if [ -z "${EXPECTED_LABELS_JSON:-}" ]; then
    echo "EXPECTED_LABELS_JSON is required" >&2
    return 1
  fi
  if [ -z "${ACTUAL_LABELS_JSON:-}" ]; then
    echo "ACTUAL_LABELS_JSON is required" >&2
    return 1
  fi
}

@test "expected labels are present in actual labels" {
  missing="$(jq -n \
    --argjson expected "$EXPECTED_LABELS_JSON" \
    --argjson actual "$ACTUAL_LABELS_JSON" \
    '$expected | map(select(. as $l | ($actual | index($l) | not)))')"

  if [ "$(jq 'length' <<< "$missing")" -ne 0 ]; then
    echo "Missing expected labels: $(jq -r 'join(", ")' <<< "$missing")"
    false
  fi
}

#!/usr/bin/env bats

@test "generated site contains fixture content" {
  run grep -F "Jekyll preset fixture" "$TEST_OUTPUT_DIRECTORY/index.html"
  [ "$status" -eq 0 ]
}

@test "nested site directory does not re-ingest stale output" {
  [ ! -e "$TEST_OUTPUT_DIRECTORY/site/stale.html" ]
}

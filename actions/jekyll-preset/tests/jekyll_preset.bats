#!/usr/bin/env bats

@test "generated site contains index.html" {
  [ -f "$TEST_OUTPUT_DIRECTORY/index.html" ]
}

@test "generated site contains fixture content" {
  run grep -F "Jekyll preset fixture" "$TEST_OUTPUT_DIRECTORY/index.html"
  [ "$status" -eq 0 ]
}

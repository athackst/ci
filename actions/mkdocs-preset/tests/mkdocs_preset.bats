#!/usr/bin/env bats

@test "site index exists" {
  [ -f "$TEST_OUTPUT_DIRECTORY/index.html" ]
}

@test "site contains fixture content" {
  run grep -F "MkDocs fixture" "$TEST_OUTPUT_DIRECTORY/index.html"
  [ "$status" -eq 0 ]
}

@test "site uses managed theme overrides" {
  run grep -F "extra.css" "$TEST_OUTPUT_DIRECTORY/index.html"
  [ "$status" -eq 0 ]
}

#!/usr/bin/env bats

@test "mkdocs.yml exists" {
  [ -f "$TEST_OUTPUT_DIRECTORY/mkdocs.yml" ]
}

@test "overrides directory and main template exist" {
  [ -d "$TEST_OUTPUT_DIRECTORY/overrides" ]
  [ -f "$TEST_OUTPUT_DIRECTORY/overrides/main.html" ]
  [ ! -e "$TEST_OUTPUT_DIRECTORY/overrides/obsolete.html" ]
}

@test "requirements includes required packages" {
  [ -f "$TEST_OUTPUT_DIRECTORY/requirements.txt" ]

  run grep -Eq '^mike([<>=!~].*)?$' "$TEST_OUTPUT_DIRECTORY/requirements.txt"
  [ "$status" -eq 0 ]

  run grep -Eq '^mkdocs-material([<>=!~].*)?$' "$TEST_OUTPUT_DIRECTORY/requirements.txt"
  [ "$status" -eq 0 ]

  run grep -F "repository-only-package" "$TEST_OUTPUT_DIRECTORY/requirements.txt"
  [ "$status" -ne 0 ]
}

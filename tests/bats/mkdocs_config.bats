#!/usr/bin/env bats

@test "mkdocs.yml exists" {
  [ -f mkdocs.yml ]
}

@test "overrides directory and main template exist" {
  [ -d overrides ]
  [ -f overrides/main.html ]
}

@test "requirements includes required packages" {
  [ -f requirements.txt ]

  run grep -Eq '^mike([<>=!~].*)?$' requirements.txt
  [ "$status" -eq 0 ]

  run grep -Eq '^mkdocs-material([<>=!~].*)?$' requirements.txt
  [ "$status" -eq 0 ]
}

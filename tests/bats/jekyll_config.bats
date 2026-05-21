#!/usr/bin/env bats

@test "_config.yml exists" {
  [ -f _config.yml ]
}

@test "Gemfile exists" {
  [ -f Gemfile ]
}

@test "semiliterate config exists" {
  [ -f semiliterate.yml ]
}

@test "_config.yml includes configured metadata" {
  run grep -F "title: CI Test Site" _config.yml
  [ "$status" -eq 0 ]

  run grep -F "description: Test description for Jekyll config" _config.yml
  [ "$status" -eq 0 ]

  run grep -F "image: https://example.com/site-preview.png" _config.yml
  [ "$status" -eq 0 ]

  run grep -F "edit_url: https://example.com/edit/" _config.yml
  [ "$status" -eq 0 ]
}

@test "_config.yml keeps versions.enabled as a boolean false by default" {
  run grep -F "versions:" _config.yml
  [ "$status" -eq 0 ]

  run grep -F "  enabled: false" _config.yml
  [ "$status" -eq 0 ]

  run grep -F "  prefix: ci" _config.yml
  [ "$status" -eq 0 ]
}

@test "merge_jekyll_config writes versions.enabled as boolean true when enabled" {
  temp_config="$(mktemp)"
  repo_root="$(cd "$BATS_TEST_DIRNAME/../.." && pwd)"

  TITLE="CI Test Site" \
  DESCRIPTION="Test description for Jekyll config" \
  IMAGE="" \
  EDIT_URL="https://example.com/edit/" \
  REPOSITORY="athackst/ci" \
  VERSIONS_ENABLED="true" \
  PREFIX="docs" \
  python3 "$repo_root/actions/jekyll-config/merge_jekyll_config.py" \
    "$repo_root/actions/jekyll-config/_config.yml" \
    "$temp_config"

  run grep -F "versions:" "$temp_config"
  [ "$status" -eq 0 ]

  run grep -F "  enabled: true" "$temp_config"
  [ "$status" -eq 0 ]

  run grep -F "  prefix: docs" "$temp_config"
  [ "$status" -eq 0 ]

  rm -f "$temp_config"
}

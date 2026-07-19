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

@test "_config.yml keeps versions disabled with no config by default" {
  run grep -F "versions:" _config.yml
  [ "$status" -eq 0 ]

  run grep -F "  enabled: false" _config.yml
  [ "$status" -eq 0 ]

  run grep -F "  config: ''" _config.yml
  [ "$status" -eq 0 ]
}

@test "merge_jekyll_config writes versions config when provided" {
  temp_config="$(mktemp)"
  action_dir="$(cd "$BATS_TEST_DIRNAME/.." && pwd)"

  TITLE="CI Test Site" \
  DESCRIPTION="Test description for Jekyll config" \
  IMAGE="" \
  EDIT_URL="https://example.com/edit/" \
  REPOSITORY="athackst/ci" \
  VERSIONS_ENABLED="true" \
  VERSIONS_CONFIG="docs/versions.json" \
  PREFIX="/ci" \
  python3 "$action_dir/merge_jekyll_config.py" \
    "$action_dir/_config.yml" \
    "$temp_config"

  run grep -F "versions:" "$temp_config"
  [ "$status" -eq 0 ]

  run grep -F "  enabled: true" "$temp_config"
  [ "$status" -eq 0 ]

  run grep -F "  config: docs/versions.json" "$temp_config"
  [ "$status" -eq 0 ]

  rm -f "$temp_config"
}

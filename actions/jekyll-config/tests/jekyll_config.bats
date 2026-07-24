#!/usr/bin/env bats

@test "_config.yml exists" {
  [ -f "$TEST_OUTPUT_DIRECTORY/_config.yml" ]
}

@test "Gemfile exists" {
  [ -f "$TEST_OUTPUT_DIRECTORY/Gemfile" ]
  [ ! -e "$TEST_OUTPUT_DIRECTORY/Gemfile.lock" ]
  run grep -F "repository-only-gem" "$TEST_OUTPUT_DIRECTORY/Gemfile"
  [ "$status" -ne 0 ]
}

@test "semiliterate config exists" {
  [ -f "$TEST_OUTPUT_DIRECTORY/semiliterate.yml" ]
}

@test "_config.yml includes configured metadata" {
  run grep -F "title: CI Test Site" "$TEST_OUTPUT_DIRECTORY/_config.yml"
  [ "$status" -eq 0 ]

  run grep -F "description: Test description for Jekyll config" "$TEST_OUTPUT_DIRECTORY/_config.yml"
  [ "$status" -eq 0 ]

  run grep -F "image: https://example.com/site-preview.png" "$TEST_OUTPUT_DIRECTORY/_config.yml"
  [ "$status" -eq 0 ]

  run grep -F "edit_url: https://example.com/edit/" "$TEST_OUTPUT_DIRECTORY/_config.yml"
  [ "$status" -eq 0 ]
}

@test "_config.yml keeps versions disabled with no config by default" {
  run grep -F "versions:" "$TEST_OUTPUT_DIRECTORY/_config.yml"
  [ "$status" -eq 0 ]

  run grep -F "  enabled: false" "$TEST_OUTPUT_DIRECTORY/_config.yml"
  [ "$status" -eq 0 ]

  run grep -F "  config: ''" "$TEST_OUTPUT_DIRECTORY/_config.yml"
  [ "$status" -eq 0 ]
}

@test "render_jekyll_config writes versions config when provided" {
  temp_config="$(mktemp)"
  action_dir="$(cd "$BATS_TEST_DIRNAME/.." && pwd)"

  TITLE="CI Test Site" \
  DESCRIPTION="Test description for Jekyll config" \
  IMAGE="" \
  EDIT_URL="https://example.com/edit/" \
  REPOSITORY="athackst/ci" \
  NAV_FILENAME=".nav.yml" \
  VERSIONS_ENABLED="true" \
  VERSIONS_CONFIG="docs/versions.json" \
  PREFIX="/ci" \
  python3 "$action_dir/render_jekyll_config.py" \
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

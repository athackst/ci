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

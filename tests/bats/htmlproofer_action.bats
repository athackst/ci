#!/usr/bin/env bats

setup() {
  [ -f "_site/index.html" ] || { echo "_site/index.html not found" >&2; return 1; }
}

@test "site artifact was extracted into _site" {
  [ -f "_site/index.html" ]
}

@test "fixture content is present" {
  run grep -q "Fixture Site" _site/index.html
  [ "$status" -eq 0 ]
}

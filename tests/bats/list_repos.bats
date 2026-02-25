#!/usr/bin/env bats

setup() {
  TEST_TMPDIR="$(mktemp -d)"
  export TEST_TMPDIR
  export CALL_COUNT_FILE="${TEST_TMPDIR}/gh_calls"
  export PATH="${TEST_TMPDIR}:$PATH"
  : > "${CALL_COUNT_FILE}"

  cat > "${TEST_TMPDIR}/gh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" >> "$CALL_COUNT_FILE"
case "$*" in
  *"page=1&per_page=100"*)
    jq -c '
      . + (
        [range(0;97) | {
          full_name: ("athackst/filler-" + (tostring)),
          private: false,
          fork: true,
          archived: false
        }]
      )
    ' tests/fixtures/list_repos/page1.json
    ;;
  *"page=2&per_page=100"*)
    cat tests/fixtures/list_repos/page2.json
    ;;
  *)
    echo "unexpected gh args: $*" >&2
    exit 1
    ;;
esac
EOF
  chmod +x "${TEST_TMPDIR}/gh"
}

teardown() {
  rm -rf "${TEST_TMPDIR}"
}

@test "list-repos filters public non-fork non-archived repos across pages" {
  run env USER="athackst" PRIVATE="false" FORK="false" ARCHIVED="false" \
    bash actions/list-repos/get_repos.sh

  [ "$status" -eq 0 ]
  [ "$output" = '["athackst/repo-public-1","athackst/repo-public-2"]' ]
}

@test "list-repos filters private repos" {
  run env USER="athackst" PRIVATE="true" FORK="false" ARCHIVED="false" \
    bash actions/list-repos/get_repos.sh

  [ "$status" -eq 0 ]
  [ "$output" = '["athackst/repo-private-1"]' ]
}

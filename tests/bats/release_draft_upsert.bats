#!/usr/bin/env bats

setup() {
  export GITHUB_REPOSITORY="owner/repo"
  export GH_CALL_LOG="${BATS_TEST_TMPDIR}/gh-calls.log"
  export PATH="${BATS_TEST_TMPDIR}/bin:${PATH}"

  mkdir -p "${BATS_TEST_TMPDIR}/bin"
  cat > "${BATS_TEST_TMPDIR}/bin/gh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

printf '%s\n' "$*" >> "$GH_CALL_LOG"

[ "${1:-}" = "api" ] || { echo "unexpected gh command" >&2; exit 1; }
shift

method="GET"
input_file=""
endpoint=""
while [ "$#" -gt 0 ]; do
  case "$1" in
    -X)
      method="$2"
      shift 2
      ;;
    --input)
      input_file="$2"
      shift 2
      ;;
    *)
      endpoint="$1"
      shift
      ;;
  esac
done

if [ "$method" = "GET" ] && [ "$endpoint" = "repos/owner/repo/releases?per_page=100" ]; then
  printf '%s\n' "$GH_RELEASES_JSON"
  exit 0
fi

if [ "$method" = "PATCH" ]; then
  release_id="${endpoint##*/}"
  jq -n \
    --argjson id "$release_id" \
    --arg name "$(jq -r '.name' "$input_file")" \
    --arg tag_name "$(jq -r '.tag_name' "$input_file")" \
    '{id: $id, name: $name, tag_name: $tag_name, draft: true}'
  exit 0
fi

if [ "$method" = "POST" ] && [ "$endpoint" = "repos/owner/repo/releases" ]; then
  jq -n \
    --arg name "$(jq -r '.name' "$input_file")" \
    --arg tag_name "$(jq -r '.tag_name' "$input_file")" \
    '{id: 900, name: $name, tag_name: $tag_name, draft: true}'
  exit 0
fi

echo "unexpected gh api call: $method $endpoint" >&2
exit 1
EOF
  chmod +x "${BATS_TEST_TMPDIR}/bin/gh"
}

run_upsert() {
  TAG_NAME="$1" \
  REUSE_EXISTING_DRAFT="${2:-true}" \
  DRAFT_RELEASE_ID="${3:-}" \
  RELEASE_NAME="Test Release" \
  CHANGELOG="Test changelog" \
  bash "${BATS_TEST_DIRNAME}/../../actions/release-draft/upsert_draft_release.sh"
}

@test "draft release id updates before tag or fallback lookup" {
  export GH_RELEASES_JSON='[
    {"id": 303, "tag_name": "v1.0.0", "draft": true, "created_at": "2024-03-01T00:00:00Z"}
  ]'

  run run_upsert "v1.0.0" "false" "303"

  [ "$status" -eq 0 ]
  [ "$(jq -r '.id' <<< "$output")" = "303" ]
  run grep -q "PATCH repos/owner/repo/releases/303" "$GH_CALL_LOG"
  [ "$status" -eq 0 ]
  run grep -q "api repos/owner/repo/releases?per_page=100" "$GH_CALL_LOG"
  [ "$status" -eq 0 ]
}

@test "published draft-release-id is ignored and a new draft is created when reuse is false" {
  export GH_RELEASES_JSON='[
    {"id": 303, "tag_name": "v1.0.0", "draft": false, "created_at": "2024-03-01T00:00:00Z"}
  ]'

  run run_upsert "v2.0.0" "false" "303"

  [ "$status" -eq 0 ]
  run grep -q '"id": 900' <<< "$output"
  [ "$status" -eq 0 ]
  run grep -q "PATCH repos/owner/repo/releases/303" "$GH_CALL_LOG"
  [ "$status" -ne 0 ]
  run grep -q "POST repos/owner/repo/releases" "$GH_CALL_LOG"
  [ "$status" -eq 0 ]
}

@test "matching tag updates matching draft release first" {
  export GH_RELEASES_JSON='[
    {"id": 101, "tag_name": "v1.0.0", "draft": true, "created_at": "2024-01-01T00:00:00Z"},
    {"id": 202, "tag_name": "v2.0.0", "draft": true, "created_at": "2024-02-01T00:00:00Z"}
  ]'

  run run_upsert "v1.0.0"

  [ "$status" -eq 0 ]
  [ "$(jq -r '.id' <<< "$output")" = "101" ]
  run grep -q "PATCH repos/owner/repo/releases/101" "$GH_CALL_LOG"
  [ "$status" -eq 0 ]
}

@test "missing tag falls back to newest existing draft release" {
  export GH_RELEASES_JSON='[
    {"id": 202, "tag_name": "v2.0.0", "draft": true, "created_at": "2024-02-01T00:00:00Z"}
  ]'

  run run_upsert "v1.0.0"

  [ "$status" -eq 0 ]
  [ "$(jq -r '.id' <<< "$output")" = "202" ]
  run grep -q "PATCH repos/owner/repo/releases/202" "$GH_CALL_LOG"
  [ "$status" -eq 0 ]
}

@test "unmatched tag updates newest existing draft release" {
  export GH_RELEASES_JSON='[
    {"id": 101, "tag_name": "v1.0.0", "draft": true, "created_at": "2024-01-01T00:00:00Z"},
    {"id": 202, "tag_name": "v2.0.0", "draft": true, "created_at": "2024-02-01T00:00:00Z"}
  ]'

  run run_upsert "v3.0.0"

  [ "$status" -eq 0 ]
  [ "$(jq -r '.id' <<< "$output")" = "202" ]
  [ "$(jq -r '.tag_name' <<< "$output")" = "v3.0.0" ]
  run grep -q "PATCH repos/owner/repo/releases/202" "$GH_CALL_LOG"
  [ "$status" -eq 0 ]
}

@test "reuse-existing-draft false creates release when tag is missing" {
  export GH_RELEASES_JSON='[
    {"id": 202, "tag_name": "v2.0.0", "draft": true, "created_at": "2024-02-01T00:00:00Z"}
  ]'

  run run_upsert "v3.0.0" "false"

  [ "$status" -eq 0 ]
  [ "$(jq -r '.id' <<< "$output")" = "900" ]
  run grep -q "POST repos/owner/repo/releases" "$GH_CALL_LOG"
  [ "$status" -eq 0 ]
  run grep -q "PATCH repos/owner/repo/releases" "$GH_CALL_LOG"
  [ "$status" -ne 0 ]
}

@test "reuse-existing-draft false still updates matching tag" {
  export GH_RELEASES_JSON='[
    {"id": 101, "tag_name": "v1.0.0", "draft": true, "created_at": "2024-01-01T00:00:00Z"}
  ]'

  run run_upsert "v1.0.0" "false"

  [ "$status" -eq 0 ]
  [ "$(jq -r '.id' <<< "$output")" = "101" ]
  run grep -q "PATCH repos/owner/repo/releases/101" "$GH_CALL_LOG"
  [ "$status" -eq 0 ]
}

#!/usr/bin/env bats

setup() {
  TEST_ROOT="$(mktemp -d)"
  TEMPLATE_DIR="$TEST_ROOT/template"
  CONSUMER_DIR="$TEST_ROOT/consumer"
  RESULT_FILE="$TEST_ROOT/result.json"
  ACTION_SCRIPT="$(cd "$BATS_TEST_DIRNAME/.." && pwd)/run_copier_copy.sh"

  mkdir -p "$TEMPLATE_DIR/template" "$CONSUMER_DIR"
  cat > "$TEMPLATE_DIR/copier.yml" <<'EOF'
_subdirectory: template
_answers_file: .copier-answers.yml
project_name:
  type: str
  default: fixture
EOF
  cat > "$TEMPLATE_DIR/template/message.txt.jinja" <<'EOF'
project: {{ project_name }}
EOF
  mkdir -p "$TEMPLATE_DIR/template/nested"
  cat > "$TEMPLATE_DIR/template/nested/file with spaces.txt" <<'EOF'
fixture with an unusual filename
EOF
  cat > "$TEMPLATE_DIR/template/{{ _copier_conf.answers_file }}.jinja" <<'EOF'
# Changes here will be overwritten by Copier; NEVER EDIT MANUALLY
{{ _copier_answers|to_nice_yaml -}}
EOF

  git -C "$TEMPLATE_DIR" init --quiet --initial-branch=main
  git -C "$TEMPLATE_DIR" config user.name "CI Test"
  git -C "$TEMPLATE_DIR" config user.email "ci-test@example.com"
  git -C "$TEMPLATE_DIR" add .
  git -C "$TEMPLATE_DIR" commit --quiet -m "Create template"
  git -C "$TEMPLATE_DIR" tag v1.0.0

  git -C "$CONSUMER_DIR" init --quiet --initial-branch=main
  git -C "$CONSUMER_DIR" config user.name "CI Test"
  git -C "$CONSUMER_DIR" config user.email "ci-test@example.com"
  git -C "$CONSUMER_DIR" commit --quiet --allow-empty -m "Create consumer"
}

teardown() {
  rm -rf "$TEST_ROOT"
}

run_copy() {
  local answers_file="$1"
  local vcs_ref="$2"
  local overwrite="$3"

  run bash -c '
    cd "$1"
    bash "$2" \
      --source "$3" \
      --destination . \
      --answers-file "$4" \
      --vcs-ref "$5" \
      --overwrite "$6" \
      --result-file "$7"
  ' _ "$CONSUMER_DIR" "$ACTION_SCRIPT" "$TEMPLATE_DIR" "$answers_file" "$vcs_ref" "$overwrite" "$RESULT_FILE"
}

@test "real Copier copy reports rendered files and custom answers file" {
  run_copy .copier-answers.custom.yml v1.0.0 true

  [ "$status" -eq 0 ]
  [ "$(jq -r '.changed' "$RESULT_FILE")" = "true" ]
  [ "$(jq -r '.changed_files | index("message.txt") != null' "$RESULT_FILE")" = "true" ]
  [ "$(jq -r '.changed_files | index("nested/file with spaces.txt") != null' "$RESULT_FILE")" = "true" ]
  [ "$(jq -r '.changed_files | index(".copier-answers.custom.yml") != null' "$RESULT_FILE")" = "true" ]
  [ "$(jq -r '.command | contains("--overwrite")' "$RESULT_FILE")" = "true" ]
  [ "$(jq -r '.command | contains("--answers-file .copier-answers.custom.yml")' "$RESULT_FILE")" = "true" ]
  grep -Fqx "project: fixture" "$CONSUMER_DIR/message.txt"
  grep -Fq "_commit: v1.0.0" "$CONSUMER_DIR/.copier-answers.custom.yml"
}

@test "repeating the same copy reports no changes" {
  run_copy .copier-answers.yml v1.0.0 true
  [ "$status" -eq 0 ]
  git -C "$CONSUMER_DIR" add .
  git -C "$CONSUMER_DIR" commit --quiet -m "Commit rendered project"

  run_copy .copier-answers.yml v1.0.0 true

  [ "$status" -eq 0 ]
  [ "$(jq -r '.changed' "$RESULT_FILE")" = "false" ]
  [ "$(jq -r '.changed_files | length' "$RESULT_FILE")" -eq 0 ]
}

@test "overwrite false fails on an existing destination file" {
  cat > "$CONSUMER_DIR/message.txt" <<'EOF'
project: consumer customization
EOF
  git -C "$CONSUMER_DIR" add message.txt
  git -C "$CONSUMER_DIR" commit --quiet -m "Add consumer file"

  run_copy .copier-answers.yml v1.0.0 false

  [ "$status" -ne 0 ]
  [ "$(jq -r '.command | contains("--overwrite")' "$RESULT_FILE")" = "false" ]
  grep -Fqx "project: consumer customization" "$CONSUMER_DIR/message.txt"
}

@test "Copier failure status is preserved for an invalid template ref" {
  run_copy .copier-answers.yml missing-template-ref true

  [ "$status" -ne 0 ]
  [ "$(jq -r '.command | contains("missing-template-ref")' "$RESULT_FILE")" = "true" ]
}

@test "dirty consumer repository fails before copying" {
  touch "$CONSUMER_DIR/existing-change.txt"

  run_copy .copier-answers.yml v1.0.0 true

  [ "$status" -eq 1 ]
  [[ "$output" == *"Destination repository is dirty"* ]]
  [ "$(jq -r '.changed' "$RESULT_FILE")" = "false" ]
  [ ! -e "$CONSUMER_DIR/message.txt" ]
}

@test "invalid overwrite input fails" {
  run_copy .copier-answers.yml v1.0.0 sometimes

  [ "$status" -eq 2 ]
  [[ "$output" == *"--overwrite must be true or false"* ]]
}

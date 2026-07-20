#!/usr/bin/env bats

setup() {
  TEST_ROOT="$(mktemp -d)"
  TEMPLATE_DIR="$TEST_ROOT/template"
  CONSUMER_DIR="$TEST_ROOT/consumer"
  RESULT_FILE="$TEST_ROOT/result.json"
  ACTION_SCRIPT="$(cd "$BATS_TEST_DIRNAME/.." && pwd)/run_copier_update.sh"
}

teardown() {
  rm -rf "$TEST_ROOT"
}

create_template() {
  mkdir -p "$TEMPLATE_DIR/template"

  cat > "$TEMPLATE_DIR/copier.yml" <<'EOF'
_subdirectory: template
_answers_file: .copier-answers.yml
project_name:
  type: str
  default: fixture
EOF

  cat > "$TEMPLATE_DIR/template/message.txt.jinja" <<'EOF'
message: baseline
project: {{ project_name }}
EOF

  cat > "$TEMPLATE_DIR/template/{{ _copier_conf.answers_file }}.jinja" <<'EOF'
# Changes here will be overwritten by Copier; NEVER EDIT MANUALLY
{{ _copier_answers|to_nice_yaml -}}
EOF

  git -C "$TEMPLATE_DIR" init --quiet --initial-branch=main
  git -C "$TEMPLATE_DIR" config user.name "CI Test"
  git -C "$TEMPLATE_DIR" config user.email "ci-test@example.com"
  git -C "$TEMPLATE_DIR" add .
  git -C "$TEMPLATE_DIR" commit --quiet -m "Create baseline template"
  git -C "$TEMPLATE_DIR" tag v1.0.0
}

create_consumer() {
  copier copy \
    --trust \
    --defaults \
    --vcs-ref v1.0.0 \
    "$TEMPLATE_DIR" \
    "$CONSUMER_DIR"

  git -C "$CONSUMER_DIR" init --quiet --initial-branch=main
  git -C "$CONSUMER_DIR" config user.name "CI Test"
  git -C "$CONSUMER_DIR" config user.email "ci-test@example.com"
  git -C "$CONSUMER_DIR" add .
  git -C "$CONSUMER_DIR" commit --quiet -m "Render baseline project"
}

update_template() {
  cat > "$TEMPLATE_DIR/template/message.txt.jinja" <<'EOF'
message: updated
project: {{ project_name }}
EOF
  cat > "$TEMPLATE_DIR/template/file with spaces.txt" <<'EOF'
fixture with an unusual filename
EOF

  git -C "$TEMPLATE_DIR" add .
  git -C "$TEMPLATE_DIR" commit --quiet -m "Update template message"
  git -C "$TEMPLATE_DIR" tag v1.1.0
}

prepare_update_fixture() {
  create_template
  create_consumer
  update_template
}

run_update() {
  local vcs_ref="$1"

  run bash -c '
    cd "$1"
    bash "$2" \
      --answers-file .copier-answers.yml \
      --vcs-ref "$3" \
      --result-file "$4"
  ' _ "$CONSUMER_DIR" "$ACTION_SCRIPT" "$vcs_ref" "$RESULT_FILE"
}

@test "missing answers file fails with empty state" {
  mkdir -p "$CONSUMER_DIR"

  run bash -c '
    cd "$1"
    bash "$2" \
      --answers-file .copier-answers.yml \
      --result-file "$3"
  ' _ "$CONSUMER_DIR" "$ACTION_SCRIPT" "$RESULT_FILE"

  [ "$status" -eq 1 ]
  [ "$(jq -r '.answers_found' "$RESULT_FILE")" = "false" ]
  [ "$(jq -r '.changed' "$RESULT_FILE")" = "false" ]
  [ "$(jq -r '.conflicts_found' "$RESULT_FILE")" = "false" ]
  [ "$(jq -r '.command' "$RESULT_FILE")" = "" ]
}

@test "real Copier update reports changed files and updates metadata" {
  prepare_update_fixture

  run_update v1.1.0

  [ "$status" -eq 0 ]
  [ "$(jq -r '.answers_found' "$RESULT_FILE")" = "true" ]
  [ "$(jq -r '.changed' "$RESULT_FILE")" = "true" ]
  [ "$(jq -r '.changed_files | index("message.txt") != null' "$RESULT_FILE")" = "true" ]
  [ "$(jq -r '.changed_files | index("file with spaces.txt") != null' "$RESULT_FILE")" = "true" ]
  [ "$(jq -r '.changed_files | index(".copier-answers.yml") != null' "$RESULT_FILE")" = "true" ]
  [ "$(jq -r '.conflicts_found' "$RESULT_FILE")" = "false" ]
  grep -Fqx "message: updated" "$CONSUMER_DIR/message.txt"
  grep -Fq "_commit: v1.1.0" "$CONSUMER_DIR/.copier-answers.yml"
}

@test "real Copier conflict fails and reports the conflicted file" {
  prepare_update_fixture

  cat > "$CONSUMER_DIR/message.txt" <<'EOF'
message: consumer customization
project: fixture
EOF
  git -C "$CONSUMER_DIR" add message.txt
  git -C "$CONSUMER_DIR" commit --quiet -m "Customize generated message"

  run_update v1.1.0

  [ "$status" -eq 1 ]
  [ "$(jq -r '.changed' "$RESULT_FILE")" = "true" ]
  [ "$(jq -r '.conflicts_found' "$RESULT_FILE")" = "true" ]
  [ "$(jq -r '.conflicted_files | index("message.txt") != null' "$RESULT_FILE")" = "true" ]
}

@test "Copier failure status is preserved for an invalid template ref" {
  create_template
  create_consumer

  run_update missing-template-ref

  [ "$status" -ne 0 ]
  [ "$(jq -r '.answers_found' "$RESULT_FILE")" = "true" ]
  [ "$(jq -r '.command | contains("missing-template-ref")' "$RESULT_FILE")" = "true" ]
}

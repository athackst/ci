#!/usr/bin/env bats

setup() {
  out_dir="$(mktemp -d)"
  [ -n "${ACTIONLINT:-}" ]
  [ -x "${ACTIONLINT}" ]
  manifest_path="${BATS_TEST_DIRNAME}/../../copier_update_paths.txt"
  [ -f "${manifest_path}" ]
}

teardown() {
  if [ -n "${out_dir:-}" ] && [ -d "${out_dir}" ]; then
    rm -rf "${out_dir}"
  fi
}

render_variant() {
  local variant="$1"

  copier copy --trust --defaults \
    --data "site_generator=${variant}" \
    --data "bump_script_path=" \
    . "${out_dir}"
}

collect_copier_managed_paths() {
  local variants=("$@")
  local variant_dir
  local rel_path
  local all_paths=()

  for variant in "${variants[@]}"; do
    variant_dir="$(mktemp -d "${out_dir}/render-${variant}.XXXXXX")"
    copier copy --trust --defaults \
      --data "site_generator=${variant}" \
      --data "bump_script_path=" \
      . "${variant_dir}" >/dev/null 2>&1

    while IFS= read -r rel_path; do
      all_paths+=("${rel_path}")
    done < <(cd "${variant_dir}" && find .github -type f | sort)
  done

  printf '%s\n' "${all_paths[@]}" | sort -u
}

@test "copier renders mkdocs variant" {
  render_variant mkdocs
  wf_dir="${out_dir}/.github/workflows"
  answers_file="${out_dir}/.copier-answers.ci.yml"

  [ -f "${wf_dir}/pr_bot.yml" ]
  [ -f "${wf_dir}/release_draft.yml" ]
  [ -f "${wf_dir}/site.yml" ]
  [ -f "${wf_dir}/ci_update.yml" ]
  [ -f "${answers_file}" ]

  run grep -q "mkdocs_site.yml@main" "${wf_dir}/site.yml"
  [ "$status" -eq 0 ]

  run grep -q "site_generator: mkdocs" "${answers_file}"
  [ "$status" -eq 0 ]

  run "$ACTIONLINT" "${wf_dir}"/*.yml
  [ "$status" -eq 0 ]
}

@test "copier skips site workflow when disabled" {
  render_variant none
  wf_dir="${out_dir}/.github/workflows"
  answers_file="${out_dir}/.copier-answers.ci.yml"

  [ -f "${wf_dir}/pr_bot.yml" ]
  [ -f "${wf_dir}/release_draft.yml" ]
  [ ! -f "${wf_dir}/site.yml" ]
  [ -f "${wf_dir}/ci_update.yml" ]
  [ -f "${answers_file}" ]

  run grep -q "site_generator: none" "${answers_file}"
  [ "$status" -eq 0 ]

  run "$ACTIONLINT" "${wf_dir}"/*.yml
  [ "$status" -eq 0 ]
}

@test "copier renders jekyll variant" {
  render_variant jekyll
  wf_dir="${out_dir}/.github/workflows"
  answers_file="${out_dir}/.copier-answers.ci.yml"

  [ -f "${wf_dir}/pr_bot.yml" ]
  [ -f "${wf_dir}/release_draft.yml" ]
  [ -f "${wf_dir}/site.yml" ]
  [ -f "${wf_dir}/ci_update.yml" ]
  [ -f "${answers_file}" ]

  run grep -q "jekyll_site.yml@main" "${wf_dir}/site.yml"
  [ "$status" -eq 0 ]

  run grep -q "site_generator: jekyll" "${answers_file}"
  [ "$status" -eq 0 ]

  run "$ACTIONLINT" "${wf_dir}"/*.yml
  [ "$status" -eq 0 ]
}

@test "copier update manifest matches rendered managed paths" {
  expected="$(cat "${manifest_path}")"

  run collect_copier_managed_paths none mkdocs jekyll
  [ "$status" -eq 0 ]

  if [ "$output" != "$expected" ]; then
    echo "Manifest mismatch."
    echo
    echo "Expected:"
    printf '%s\n' "$expected"
    echo
    echo "Actual:"
    printf '%s\n' "$output"
    false
  fi
}

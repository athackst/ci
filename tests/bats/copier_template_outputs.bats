#!/usr/bin/env bats

setup() {
  out_dir="$(mktemp -d)"
  [ -n "${ACTIONLINT:-}" ]
  [ -x "${ACTIONLINT}" ]
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

@test "copier renders mkdocs variant" {
  render_variant mkdocs
  wf_dir="${out_dir}/.github/workflows"

  [ -f "${wf_dir}/pr_bot.yml" ]
  [ -f "${wf_dir}/release_draft.yml" ]
  [ -f "${wf_dir}/site.yml" ]
  [ -f "${wf_dir}/ci_update.yml" ]

  run grep -q "mkdocs_site.yml@main" "${wf_dir}/site.yml"
  [ "$status" -eq 0 ]

  run "$ACTIONLINT" "${wf_dir}"/*.yml
  [ "$status" -eq 0 ]
}

@test "copier renders jekyll variant" {
  render_variant jekyll
  wf_dir="${out_dir}/.github/workflows"

  [ -f "${wf_dir}/pr_bot.yml" ]
  [ -f "${wf_dir}/release_draft.yml" ]
  [ -f "${wf_dir}/site.yml" ]
  [ -f "${wf_dir}/ci_update.yml" ]

  run grep -q "jekyll_site.yml@main" "${wf_dir}/site.yml"
  [ "$status" -eq 0 ]

  run "$ACTIONLINT" "${wf_dir}"/*.yml
  [ "$status" -eq 0 ]
}

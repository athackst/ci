#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

SOURCE="${CI_TEMPLATE_SOURCE:-${REPO_ROOT}}"
DESTINATION="."
REPO=""
SECRET_NAME="CI_BOT_TOKEN"
SECRET_MODE="ask"
COPIER_ARGS=()

usage() {
  cat <<'EOF'
Usage: tools/init_ci_repo.sh [options] [-- copier args...]

Apply the CI Copier template to a repository and optionally set CI_BOT_TOKEN.

Options:
  --repo OWNER/REPO        GitHub repository used when setting the secret.
  --destination PATH       Directory to apply the template into. Default: .
  --source SOURCE          Copier template source. Default: this repository.
  --secret-name NAME       Secret name to set. Default: CI_BOT_TOKEN.
  --set-secret            Set the secret without prompting.
  --skip-secret           Do not prompt for or set the secret.
  -h, --help              Show this help.

Any arguments after -- are passed through to copier copy.

Examples:
  tools/init_ci_repo.sh --repo owner/repo
  tools/init_ci_repo.sh --repo owner/repo -- --data site_generator=none
EOF
}

die() {
  echo "error: $*" >&2
  exit 1
}

need_command() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

confirm() {
  local prompt="$1"
  local answer

  if [ ! -t 0 ]; then
    return 1
  fi

  read -r -p "${prompt} [y/N] " answer
  case "${answer}" in
    y|Y|yes|YES) return 0 ;;
    *) return 1 ;;
  esac
}

infer_repo() {
  local destination="$1"
  local remote_name
  local remote_url

  if [ -n "${REPO}" ]; then
    printf '%s\n' "${REPO}"
    return
  fi

  if ! git -C "${destination}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    infer_repo_with_gh "${destination}"
    return
  fi

  if remote_url="$(git -C "${destination}" remote get-url origin 2>/dev/null)"; then
    infer_repo_from_remote_url "${remote_url}" && return
  fi

  while IFS= read -r remote_name; do
    if remote_url="$(git -C "${destination}" remote get-url "${remote_name}" 2>/dev/null)"; then
      infer_repo_from_remote_url "${remote_url}" && return
    fi
  done < <(git -C "${destination}" remote)

  infer_repo_with_gh "${destination}"
}

infer_repo_from_remote_url() {
  local remote_url="$1"

  case "${remote_url}" in
    git@github.com:*.git)
      remote_url="${remote_url#git@github.com:}"
      remote_url="${remote_url%.git}"
      ;;
    git@github.com:*)
      remote_url="${remote_url#git@github.com:}"
      ;;
    git@*:*.git)
      remote_url="${remote_url#*:}"
      remote_url="${remote_url%.git}"
      ;;
    git@*:*)
      remote_url="${remote_url#*:}"
      ;;
    https://github.com/*.git)
      remote_url="${remote_url#https://github.com/}"
      remote_url="${remote_url%.git}"
      ;;
    https://github.com/*)
      remote_url="${remote_url#https://github.com/}"
      ;;
    ssh://git@github.com/*.git)
      remote_url="${remote_url#ssh://git@github.com/}"
      remote_url="${remote_url%.git}"
      ;;
    ssh://git@github.com/*)
      remote_url="${remote_url#ssh://git@github.com/}"
      ;;
    *)
      return 1
      ;;
  esac

  remote_url="${remote_url%/}"
  [ -n "${remote_url}" ] || return 1
  printf '%s\n' "${remote_url}"
}

infer_repo_with_gh() {
  local destination="$1"

  command -v gh >/dev/null 2>&1 || return 1
  (
    cd "${destination}"
    gh repo view --json nameWithOwner --jq .nameWithOwner 2>/dev/null
  )
}

set_secret() {
  local repo="$1"
  local secret_name="$2"
  local repo_name
  local repo_owner
  local token

  need_command gh

  if [ -z "${repo}" ]; then
    die "Unable to determine GitHub repository. Pass --repo OWNER/REPO to set ${secret_name}."
  fi

  repo_owner="${repo%%/*}"
  repo_name="${repo#*/}"

  cat <<EOF
${secret_name} should be a fine-grained personal access token that can maintain
the generated CI workflows for ${repo}. GitHub can prefill the token form here:

  https://github.com/settings/personal-access-tokens/new?name=${secret_name}&target_name=${repo_owner}

Limit repository access to ${repo}.

Required repository permissions:
  - Actions: Read and write
  - Contents: Read and write
  - Issues: Read and write
  - Pull requests: Read and write
  - Variables: Read and write
  - Workflows: Read and write

After the token is created, paste it below. It will be saved as the
${secret_name} Actions secret in ${repo}.
EOF

  read -r -s -p "Token: " token
  echo

  if [ -z "${token}" ]; then
    die "Secret value cannot be empty."
  fi

  printf '%s' "${token}" | gh secret set "${secret_name}" --repo "${repo}" --body-file -
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo)
      [ "$#" -ge 2 ] || die "--repo requires OWNER/REPO"
      REPO="$2"
      shift 2
      ;;
    --destination)
      [ "$#" -ge 2 ] || die "--destination requires PATH"
      DESTINATION="$2"
      shift 2
      ;;
    --source)
      [ "$#" -ge 2 ] || die "--source requires SOURCE"
      SOURCE="$2"
      shift 2
      ;;
    --secret-name)
      [ "$#" -ge 2 ] || die "--secret-name requires NAME"
      SECRET_NAME="$2"
      shift 2
      ;;
    --set-secret)
      SECRET_MODE="set"
      shift
      ;;
    --skip-secret)
      SECRET_MODE="skip"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      COPIER_ARGS=("$@")
      break
      ;;
    *)
      die "Unknown argument: $1"
      ;;
  esac
done

need_command copier

mkdir -p "${DESTINATION}"

echo "Applying CI template from ${SOURCE} to ${DESTINATION}..."
copier copy --trust --vcs-ref HEAD "${COPIER_ARGS[@]}" "${SOURCE}" "${DESTINATION}"

RESOLVED_REPO="$(infer_repo "${DESTINATION}")"

case "${SECRET_MODE}" in
  set)
    set_secret "${RESOLVED_REPO}" "${SECRET_NAME}"
    ;;
  skip)
    echo "Skipped ${SECRET_NAME} setup."
    ;;
  ask)
    if confirm "Set ${SECRET_NAME}${RESOLVED_REPO:+ for ${RESOLVED_REPO}} now?"; then
      set_secret "${RESOLVED_REPO}" "${SECRET_NAME}"
    else
      echo "Skipped ${SECRET_NAME} setup."
    fi
    ;;
esac

echo "CI template initialization complete."

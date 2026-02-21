#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Initialize a repository to use athackst/ci workflows.

What this script does:
1) Applies the CI Copier template to the current repository.
2) Sets CI_BOT_TOKEN as a GitHub Actions secret on the repository.

Usage:
  tools/init_ci_repo.sh [options]

Options:
  --repo <owner/repo>         Repository slug. Auto-detected if omitted.
  --source <copier-source>    Copier source (default: gh:athackst/ci).
  --template-ref <ref>        Copier vcs ref (default: main).
  --secret-name <name>        Secret name to set (default: CI_BOT_TOKEN).
  --token-file <path>         Read token value from file.
  --skip-secret               Skip setting the GitHub secret.
  --help                      Show this help.

Token input precedence:
1) --token-file
2) CI_BOT_TOKEN env var
3) interactive prompt

Example:
  CI_BOT_TOKEN=ghp_xxx tools/init_ci_repo.sh --repo athackst/my-repo
EOF
}

require_cmd() {
  local cmd="$1"
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "Missing required command: $cmd" >&2
    exit 1
  }
}

REPO=""
SOURCE="gh:athackst/ci"
TEMPLATE_REF="main"
SECRET_NAME="CI_BOT_TOKEN"
TOKEN_FILE=""
SKIP_SECRET="false"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      REPO="${2:-}"
      shift 2
      ;;
    --source)
      SOURCE="${2:-}"
      shift 2
      ;;
    --template-ref)
      TEMPLATE_REF="${2:-}"
      shift 2
      ;;
    --secret-name)
      SECRET_NAME="${2:-}"
      shift 2
      ;;
    --token-file)
      TOKEN_FILE="${2:-}"
      shift 2
      ;;
    --skip-secret)
      SKIP_SECRET="true"
      shift 1
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

require_cmd gh
require_cmd copier
require_cmd git

if [[ -z "$REPO" ]]; then
  if gh repo view --json nameWithOwner --jq .nameWithOwner >/dev/null 2>&1; then
    REPO="$(gh repo view --json nameWithOwner --jq .nameWithOwner)"
  else
    echo "--repo was not provided and repo auto-detect failed." >&2
    exit 1
  fi
fi

echo "Repo: $REPO"
echo "Copier source: $SOURCE"
echo "Copier ref: $TEMPLATE_REF"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Working tree is dirty. Commit/stash changes before running init." >&2
  exit 1
fi

echo "Applying template with Copier..."
copier copy --trust --defaults --vcs-ref "$TEMPLATE_REF" "$SOURCE" .

if [[ "$SKIP_SECRET" == "true" ]]; then
  echo "Skipping secret setup (--skip-secret)."
  exit 0
fi

TOKEN_VALUE="${CI_BOT_TOKEN:-}"
if [[ -n "$TOKEN_FILE" ]]; then
  [[ -f "$TOKEN_FILE" ]] || {
    echo "Token file not found: $TOKEN_FILE" >&2
    exit 1
  }
  TOKEN_VALUE="$(<"$TOKEN_FILE")"
fi

if [[ -z "$TOKEN_VALUE" ]]; then
  read -r -s -p "Enter value for $SECRET_NAME: " TOKEN_VALUE
  echo
fi

# Normalize common file/input artifacts:
# - trim trailing newlines / carriage returns
# - trim leading/trailing spaces and tabs
TOKEN_VALUE="$(printf '%s' "$TOKEN_VALUE" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"

if [[ -z "$TOKEN_VALUE" ]]; then
  echo "Token value is empty; refusing to set secret." >&2
  exit 1
fi

echo "Setting secret '$SECRET_NAME' on $REPO..."
gh secret set "$SECRET_NAME" --repo "$REPO" --body "$TOKEN_VALUE"
echo "Done."

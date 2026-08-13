#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${GITHUB_WORKSPACE:-/github/workspace}"
CONFIG_DIRECTORY="/workspace/mkdocs"
TEMPLATE_DIRECTORY="/opt/mkdocs-preset"
COMMAND="${1:-serve}"

if [[ $# -gt 0 ]]; then
  shift
fi

DOCS_DIR="/tmp/docs"
SITE_DIR="site"
SITE_NAME="${GITHUB_REPOSITORY:-}"
REPO_URL=""
SITE_URL=""
EDIT_URI="edit/main/"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --docs-dir|--site-dir|--site-name|--repo-url|--site-url|--edit-uri)
      [[ $# -ge 2 ]] || { echo "Missing value for $1" >&2; exit 2; }
      key="${1#--}"
      value="$2"
      case "$key" in
        docs-dir) DOCS_DIR="$value" ;;
        site-dir) SITE_DIR="$value" ;;
        site-name) SITE_NAME="$value" ;;
        repo-url) REPO_URL="$value" ;;
        site-url) SITE_URL="$value" ;;
        edit-uri) EDIT_URI="$value" ;;
      esac
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

resolve_workspace_path() {
  local path="$1"
  if [[ "$path" = /* ]]; then
    printf '%s\n' "$path"
  else
    printf '%s/%s\n' "$WORKSPACE" "$path"
  fi
}

WORKSPACE_PATH="$(realpath -m "$WORKSPACE")"
DOCS_PATH="$(realpath -m "$(resolve_workspace_path "$DOCS_DIR")")"
SITE_PATH="$(realpath -m "$(resolve_workspace_path "$SITE_DIR")")"

case "$SITE_PATH" in
  "$WORKSPACE_PATH"/*|/tmp/*)
    ;;
  *)
    echo "Site directory must be below the workspace or under /tmp: $SITE_PATH" >&2
    exit 2
    ;;
esac

if [[ "$SITE_PATH" = "$WORKSPACE_PATH" || "$SITE_PATH" = "/tmp" ]]; then
  echo "Refusing to use the workspace or /tmp root as the site directory: $SITE_PATH" >&2
  exit 2
fi

case "$DOCS_PATH" in
  "$SITE_PATH"|"$SITE_PATH"/*)
    echo "Site directory must not equal or contain the documentation directory: $SITE_PATH" >&2
    exit 2
    ;;
esac

if [[ -z "$SITE_NAME" ]]; then
  SITE_NAME="$(basename "$WORKSPACE")"
fi

if [[ -z "$REPO_URL" ]]; then
  remote_url="$(git -C "$WORKSPACE" config --get remote.origin.url 2>/dev/null || true)"
  if [[ "$remote_url" =~ ^git@github\.com:(.+)\.git$ ]]; then
    REPO_URL="https://github.com/${BASH_REMATCH[1]}"
  elif [[ "$remote_url" =~ ^https://github\.com/(.+)$ ]]; then
    repository="${BASH_REMATCH[1]}"
    repository="${repository%.git}"
    REPO_URL="https://github.com/${repository}"
  fi
fi

if [[ -z "$REPO_URL" && -n "${GITHUB_REPOSITORY:-}" ]]; then
  REPO_URL="https://github.com/${GITHUB_REPOSITORY}"
fi

if [[ ! -d "$WORKSPACE" ]]; then
  echo "Workspace does not exist: $WORKSPACE" >&2
  exit 1
fi

mkdir -p "${DOCS_PATH}"
rm -rf "$CONFIG_DIRECTORY"
mkdir -p "$CONFIG_DIRECTORY"
cp "$TEMPLATE_DIRECTORY/requirements.txt" "$CONFIG_DIRECTORY/requirements.txt"
cp -R "$TEMPLATE_DIRECTORY/overrides" "$CONFIG_DIRECTORY/overrides"

python "$TEMPLATE_DIRECTORY/render_mkdocs_config.py" \
  --template "$TEMPLATE_DIRECTORY/mkdocs.yml.in" \
  --output "$CONFIG_DIRECTORY/mkdocs.yml" \
  --docs-dir "$DOCS_PATH" \
  --site-dir "$SITE_PATH" \
  --overrides-dir "$CONFIG_DIRECTORY/overrides" \
  --site-name "$SITE_NAME" \
  --repo-url "$REPO_URL" \
  --site-url "$SITE_URL" \
  --edit-uri "$EDIT_URI"

cd "$WORKSPACE"

case "$COMMAND" in
  build)
    mkdir -p "$SITE_PATH"
    find "$SITE_PATH" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +
    echo "Building site to $SITE_PATH"
    echo "Using mkdocs config: $CONFIG_DIRECTORY/mkdocs.yml"
    cat "$CONFIG_DIRECTORY/mkdocs.yml"
    mkdocs build --clean --config-file "$CONFIG_DIRECTORY/mkdocs.yml"
    if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
      echo "site-path=$SITE_DIR" | tee -a "$GITHUB_OUTPUT"
    fi
    ;;
  serve)
    exec mkdocs serve --config-file "$CONFIG_DIRECTORY/mkdocs.yml" --dev-addr "${DEV_ADDR:-0.0.0.0:8000}"
    ;;
  *)
    echo "Unknown command: $COMMAND (expected build or serve)" >&2
    exit 2
    ;;
esac

#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${GITHUB_WORKSPACE:-/github/workspace}"
CONFIG_DIRECTORY="/workspace/jekyll"
PRESET_DIRECTORY="/opt/jekyll-preset"
COMMAND="${1:-serve}"

if [[ $# -gt 0 ]]; then
  shift
fi

SOURCE_DIR="."
SITE_DIR="_site"
TITLE="${GITHUB_REPOSITORY:-}"
DESCRIPTION=""
IMAGE=""
EDIT_URL=""
REPOSITORY="${GITHUB_REPOSITORY:-}"
NAV_FILENAME=".nav.yml"
VERSIONS_CONFIG=""
BASE_PATH=""
BASE_URL=""
SEMILITERATE="true"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source|--site-dir|--title|--description|--image|--edit-url|--repository|--nav-filename|--versions-config|--base-path|--base-url|--semiliterate)
      [[ $# -ge 2 ]] || { echo "Missing value for $1" >&2; exit 2; }
      key="${1#--}"
      value="$2"
      case "$key" in
        source) SOURCE_DIR="$value" ;;
        site-dir) SITE_DIR="$value" ;;
        title) TITLE="$value" ;;
        description) DESCRIPTION="$value" ;;
        image) IMAGE="$value" ;;
        edit-url) EDIT_URL="$value" ;;
        repository) REPOSITORY="$value" ;;
        nav-filename) NAV_FILENAME="$value" ;;
        versions-config) VERSIONS_CONFIG="$value" ;;
        base-path) BASE_PATH="$value" ;;
        base-url) BASE_URL="$value" ;;
        semiliterate) SEMILITERATE="$value" ;;
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
SOURCE_PATH="$(realpath -m "$(resolve_workspace_path "$SOURCE_DIR")")"
SITE_PATH="$(realpath -m "$(resolve_workspace_path "$SITE_DIR")")"

if [[ ! -d "$SOURCE_PATH" ]]; then
  echo "Source directory does not exist: $SOURCE_PATH" >&2
  exit 1
fi

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

case "$SEMILITERATE" in
  true|false)
    ;;
  *)
    echo "semiliterate must be true or false: $SEMILITERATE" >&2
    exit 2
    ;;
esac

if [[ -z "$REPOSITORY" ]]; then
  remote_url="$(git -C "$WORKSPACE" config --get remote.origin.url 2>/dev/null || true)"
  if [[ "$remote_url" =~ ^git@github\.com:(.+)\.git$ ]]; then
    REPOSITORY="${BASH_REMATCH[1]}"
  elif [[ "$remote_url" =~ ^https://github\.com/(.+?)(\.git)?$ ]]; then
    REPOSITORY="${BASH_REMATCH[1]}"
  fi
fi

if [[ -z "$TITLE" ]]; then
  TITLE="${REPOSITORY:-$(basename "$WORKSPACE")}"
fi

if [[ -z "$EDIT_URL" && -n "$REPOSITORY" ]]; then
  EDIT_URL="https://www.github.com/${REPOSITORY}/edit/main/"
fi

rm -rf "$CONFIG_DIRECTORY"
mkdir -p "$CONFIG_DIRECTORY"

python "$PRESET_DIRECTORY/render_jekyll_config.py" \
  --template "$PRESET_DIRECTORY/_config.yml.in" \
  --output "$CONFIG_DIRECTORY/_config.yml" \
  --title "$TITLE" \
  --description "$DESCRIPTION" \
  --image "$IMAGE" \
  --edit-url "$EDIT_URL" \
  --repository "$REPOSITORY" \
  --nav-filename "$NAV_FILENAME" \
  --versions-config "$VERSIONS_CONFIG" \
  --base-path "$BASE_PATH"

BUILD_SOURCE="$SOURCE_PATH"
EXTRACTED_SOURCE=""
if [[ "$SEMILITERATE" = "true" ]]; then
  EXTRACTED_SOURCE="$(mktemp -d /tmp/jekyll-source.XXXXXX)"
  trap 'rm -rf -- "$EXTRACTED_SOURCE"' EXIT
  semiliterate build \
    --source "$SOURCE_PATH" \
    --out "$EXTRACTED_SOURCE" \
    --config "$PRESET_DIRECTORY/semiliterate.yml" \
    --include-mode copy \
    --verbose
  BUILD_SOURCE="$EXTRACTED_SOURCE"
fi

mkdir -p "$SITE_PATH"
find "$SITE_PATH" -mindepth 1 -maxdepth 1 -exec rm -rf -- {} +

JEKYLL_ARGS=(
  --source "$BUILD_SOURCE"
  --destination "$SITE_PATH"
  --config "$CONFIG_DIRECTORY/_config.yml"
)
if [[ -n "$BASE_URL" ]]; then
  JEKYLL_ARGS+=(--baseurl "$BASE_URL")
fi

cd "$WORKSPACE"

case "$COMMAND" in
  build)
    export JEKYLL_ENV="${JEKYLL_ENV:-production}"
    bundle exec jekyll build "${JEKYLL_ARGS[@]}"
    if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
      echo "site-path=$SITE_DIR" | tee -a "$GITHUB_OUTPUT"
    fi
    ;;
  serve)
    export JEKYLL_ENV="${JEKYLL_ENV:-development}"
    exec bundle exec jekyll serve \
      "${JEKYLL_ARGS[@]}" \
      --host "${JEKYLL_HOST:-0.0.0.0}" \
      --port "${JEKYLL_PORT:-4000}" \
      --livereload
    ;;
  *)
    echo "Unknown command: $COMMAND (expected build or serve)" >&2
    exit 2
    ;;
esac

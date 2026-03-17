#!/usr/bin/env bash
set -euo pipefail

USER="${USER:?USER is required}"
PUBLIC="${PUBLIC:-true}"
PRIVATE="${PRIVATE:-true}"
FORK="${FORK:-true}"
ARCHIVED="${ARCHIVED:-true}"
FILTER_PATHS="${FILTER_PATHS:-}"

page=1
repositories='[]'
owner_type="$(gh api "/users/${USER}" --jq '.type')"

if [[ "$owner_type" != "User" ]]; then
  echo "Expected GitHub user, got: ${owner_type}" >&2
  exit 1
fi

if [[ "$PUBLIC" == "false" && "$PRIVATE" == "false" ]]; then
  echo "[]"
  exit 0
fi

matches_filter_paths() {
  local full_name="$1"
  local filter_path

  if [[ -z "$FILTER_PATHS" ]]; then
    return 0
  fi

  while IFS= read -r filter_path; do
    if [[ -z "$filter_path" ]]; then
      continue
    fi

    if gh api "/repos/${full_name}/contents/${filter_path}" >/dev/null 2>&1; then
      return 0
    fi
  done <<< "$FILTER_PATHS"

  return 1
}

while :; do
  if [[ "$PRIVATE" == "false" && "$PUBLIC" == "true" ]]; then
    response="$(gh api "/users/${USER}/repos?page=${page}&per_page=100")"
    response_items="$response"
  else
    if response="$(gh api "/user/repos?visibility=all&affiliation=owner&page=${page}&per_page=100" 2>/dev/null)"; then
      response_items="$response"
    else
      response="$(gh api "/installation/repositories?page=${page}&per_page=100")"
      response_items="$(jq -c '.repositories' <<< "$response")"
    fi
  fi

  page_repositories="$(
    jq -c \
      --arg owner "$USER" \
      --arg public "$PUBLIC" \
      --arg private "$PRIVATE" \
      --arg fork "$FORK" \
      --arg archived "$ARCHIVED" \
      '[.[]
        | select((.owner.login // (.full_name | split("/")[0]) // "") == $owner)
        | select(($public == "true" and (.private | not)) or ($private == "true" and .private))
        | select($fork == "true" or (.fork | not))
        | select($archived == "true" or (.archived | not))
        | {
            owner: (.owner.login // (.full_name | split("/")[0])),
            name: (.name // (.full_name | split("/")[1])),
            full_name: .full_name,
            private: .private,
            fork: .fork,
            archived: .archived
          }
      ]' \
      <<< "$response_items"
  )"
  repositories="$(
    jq -nc \
      --argjson repos_acc "$repositories" \
      --argjson page_items "$page_repositories" \
      '$repos_acc + $page_items'
  )"

  if [[ "$(jq '. | length' <<< "$response_items")" -lt 100 ]]; then
    break
  fi

  page=$((page + 1))
done

if [[ -n "$FILTER_PATHS" ]]; then
  filtered_repositories='[]'

  while IFS= read -r repository; do
    full_name="$(jq -r '.full_name' <<< "$repository")"
    if matches_filter_paths "$full_name"; then
      filtered_repositories="$(
        jq -nc \
          --argjson repos_acc "$filtered_repositories" \
          --argjson repo "$repository" \
          '$repos_acc + [$repo]'
      )"
    fi
  done < <(jq -c '.[]' <<< "$repositories")

  repositories="$filtered_repositories"
fi

echo "$repositories"

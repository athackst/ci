#!/usr/bin/env bash
set -euo pipefail

USER="${USER:?USER is required}"
PRIVATE="${PRIVATE:-false}"
FORK="${FORK:-false}"
ARCHIVED="${ARCHIVED:-false}"

page=1
repositories='[]'

while :; do
  response="$(gh api "/users/${USER}/repos?page=${page}&per_page=100")"
  page_repositories="$(
    jq -c \
      --argjson private "$PRIVATE" \
      --argjson fork "$FORK" \
      --argjson archived "$ARCHIVED" \
      '[.[] | select(.private == $private and .fork == $fork and .archived == $archived) | .full_name]' \
      <<< "$response"
  )"
  repositories="$(
    jq -nc \
      --argjson repos_acc "$repositories" \
      --argjson page_items "$page_repositories" \
      '$repos_acc + $page_items'
  )"

  if [[ "$(jq '. | length' <<< "$response")" -lt 100 ]]; then
    break
  fi

  page=$((page + 1))
done

echo "$repositories"

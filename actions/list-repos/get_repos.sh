#!/usr/bin/env bash
set -euo pipefail

USER="${USER:?USER is required}"
PRIVATE="${PRIVATE:-false}"
FORK="${FORK:-false}"
ARCHIVED="${ARCHIVED:-false}"

page=1
repositories='[]'
owner_type="$(gh api "/users/${USER}" --jq '.type')"

if [[ "$owner_type" != "User" ]]; then
  echo "Expected GitHub user, got: ${owner_type}" >&2
  exit 1
fi

while :; do
  if [[ "$PRIVATE" == "true" ]]; then
    response="$(gh api "/user/repos?visibility=all&affiliation=owner&page=${page}&per_page=100")"
  else
    response="$(gh api "/users/${USER}/repos?page=${page}&per_page=100")"
  fi

  page_repositories="$(
    jq -c \
      --arg owner "$USER" \
      --argjson private "$PRIVATE" \
      --argjson fork "$FORK" \
      --argjson archived "$ARCHIVED" \
      '[.[]
        | select((.owner.login // (.full_name | split("/")[0]) // "") == $owner)
        | select(.private == $private and .fork == $fork and .archived == $archived)
        | .full_name
      ]' \
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

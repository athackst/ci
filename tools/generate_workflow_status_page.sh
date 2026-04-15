#!/usr/bin/env bash

export GH_TOKEN="$(gh auth token)"
gh api graphql -f query='{ rateLimit { limit remaining resetAt cost } }'

python3 actions/list-repos/list_repos.py \
  --debug-timing \
  --user athackst \
  --fork false \
  --archived false \
  --private false \
  --filter-path .copier-answers.ci.yml > /tmp/repositories.json

python3 .github/scripts/generate_workflow_status.py --repos-file /tmp/repositories.json
gh api graphql -f query='{ rateLimit { limit remaining resetAt cost } }'

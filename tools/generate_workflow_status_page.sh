#!/usr/bin/env bash

python3 actions/list-repos/list_repos.py \
  --user athackst \
  --fork false \
  --archived false \
  --filter-path .copier-answers.ci.yml > /tmp/repositories.json

python3 .github/scripts/generate_workflow_status.py --repos-file /tmp/repositories.json --visibility public

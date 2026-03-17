#!/usr/bin/env bash

USER=athackst \
FORK=false \
ARCHIVED=false \
FILTER_PATHS=.copier-answers.ci.yml \
actions/list-repos/get_repos.sh > /tmp/repositories.json

python3 .github/scripts/generate_workflow_status.py --repos-file /tmp/repositories.json --visibility public

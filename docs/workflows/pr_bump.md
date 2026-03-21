# PR Bump

Resolve version metadata and optionally run a repository-specific bump script that either pushes changes back to a PR branch or opens a bump PR.

## Usage

```yaml
jobs:
  pr-bump:
    uses: athackst/ci/.github/workflows/pr_bump.yml@main
    with:
      bump-script: scripts/bump_version.sh
    secrets:
      token: ${{ secrets.CI_BOT_TOKEN }}
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `configuration-path` | (optional) Path to the unified CI config file. | `.github/ci-config.yml` |
| `bump-script` | (optional) Script path to run after version resolution. | `""` |
| `push-branch` | (optional) Branch override for pushing bump commits or opening bump PRs. | PR head branch for `pull_request`; otherwise `ci/pr-bump` |

## Secrets

| Name | Description | Default |
| --- | --- | --- |
| `token` | (optional) Token used for checkout, version resolution, comment updates, and pushing bump commits. | `${{ github.token }}` |

## Outputs

| Name | Description |
| --- | --- |
| `changed` | Whether the bump script produced changes that were prepared for push or a bump PR. |
| `version` | Resolved semantic version, if any. |
| `branch` | Branch that received the bump commit or was used for the bump PR, if any. |

## Permissions

- Requires `contents: write` to push bump commits.
- Requires `pull-requests: write` to update the PR comment or open/update a bump PR.

## Advanced

- Does nothing if `bump-script` is empty.
- Resolves version metadata from the shared CI config before running the bump script.
- Exposes `FROM_REF`, `VERSION`, `MAJOR_VERSION`, `MINOR_VERSION`, `PATCH_VERSION`, and `PR_INFO_PATH` to the bump script.
- On `pull_request`, pushes to `push-branch` if set; otherwise it uses the PR head branch.
- On other events, opens or updates a PR from `push-branch` if set; otherwise it uses `ci/pr-bump`.
- Non-`pull_request` bump PRs are labeled `automerge` and `skip-changelog`.
- Maintains a single updatable PR comment for bump results.

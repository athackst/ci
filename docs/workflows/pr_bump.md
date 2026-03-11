# PR Bump

Resolve version metadata for a pull request and optionally run a repository-specific bump script that commits and pushes changes.

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
| `push-branch` | (optional) Branch override for pushing bump commits. | PR head branch |

## Secrets

| Name | Description | Default |
| --- | --- | --- |
| `token` | (optional) Token used for checkout, version resolution, comment updates, and pushing bump commits. | `${{ github.token }}` |

## Outputs

| Name | Description |
| --- | --- |
| `changed` | Whether the bump script produced changes that were committed and pushed. |
| `version` | Resolved semantic version, if any. |

## Permissions

- Requires `contents: write` to push bump commits.
- Requires `pull-requests: write` to update the PR comment when a bump commit is created.

## Advanced

- Does nothing if `bump-script` is empty.
- Resolves version metadata from the shared CI config before running the bump script.
- Exposes `FROM_REF`, `VERSION`, `MAJOR_VERSION`, `MINOR_VERSION`, `PATCH_VERSION`, and `PR_INFO_PATH` to the bump script.
- Pushes to `push-branch` if set; otherwise it uses the PR head branch.
- Maintains a single updatable PR comment for bump results.

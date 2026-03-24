# CI Updater

Run `copier update`, open or update a template-sync PR, and refresh repository labels from the shared CI config.

## Usage

```yaml
jobs:
  ci-update:
    uses: athackst/ci/.github/workflows/ci_updater.yml@main
    secrets:
      token: ${{ secrets.CI_BOT_TOKEN }}
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `create-pr` | (optional) Create or update a PR with template changes. | `true` |
| `automerge` | (optional) Add the `automerge` label to the updater PR. | `false` |
| `pr-branch` | (optional) Branch name used for template updates. | `ci/update-ci-template` |
| `pr-title` | (optional) Pull request title. | `chore: update CI template` |
| `commit-message` | (optional) Commit message for template updates. | `chore: apply CI template update` |

## Secrets

| Name | Description | Default |
| --- | --- | --- |
| `token` | (optional) Token used for checkout, push, PR operations, issue creation, and label setup. | `${{ github.token }}` |

## Outputs

| Name | Description |
| --- | --- |
| `changed` | Whether `create-pull-request` created or updated a PR. |
| `branch` | Branch name returned by `create-pull-request`, if any. |
| `pr-url` | URL for the updater PR, if any. |

## Permissions

- Requires `contents: write`, `pull-requests: write`, `issues: write`, and `actions: write`.
- `actions: write` is needed in this environment when template updates modify `.github/workflows/*`.

## Advanced

- Skips the Copier update entirely when `.copier-answers.ci.yml` is missing.
- Runs `setup-labels` against `.github/ci-config.yml` after applying template updates.
- Creates a failure issue with updater context and setup-labels outputs if the workflow fails.
- Writes a final workflow summary for both the Copier PR path and label setup results.

## Examples

Disable PR creation and just validate the update path:

```yaml
jobs:
  ci-update:
    uses: athackst/ci/.github/workflows/ci_updater.yml@main
    with:
      create-pr: false
    secrets:
      token: ${{ secrets.CI_BOT_TOKEN }}
```

# CI Updater

Run the CI template updater compatibility workflow.

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
| `automerge` | (optional) Deprecated. Retained for compatibility; updater PRs are labeled automatically. | `false` |
| `pr-branch` | (optional) Branch name used for template updates. | `ci/update-ci-template` |
| `checkout-ref` | (optional) Git ref to check out before applying template updates. | `""` |

## Secrets

| Name | Description | Required |
| --- | --- | --- |
| `token` | (optional) Token used for checkout, push, PR operations, failure issue maintenance, and label setup. | No |

## Outputs

| Name | Description |
| --- | --- |
| `changed` | Whether template changes were produced by Copier. |
| `changed-files` | Newline-delimited list of Copier-managed files changed by the update. |
| `branch` | Branch name used for the update, whether a PR was created or changes were pushed directly. |
| `pr-url` | URL for the updater PR, if one was created or updated. |

## Permissions

- Requires `contents: write`, `pull-requests: write`, `issues: write`, and `actions: write`.
- `actions: write` is needed in this environment when template updates modify `.github/workflows/*`.

## Advanced

- Wraps [`copier_update.yml`](copier_update.md) with CI-template defaults for existing consumers.
- Uses `.copier-answers.ci.yml` as the Copier answers file.
- Only changes under `.github/` and `.copier-answers.ci.yml` count toward the `changed` output, so other files do not open an update PR.
- Updater PRs use the title `chore: update CI template`, commit message `chore: apply CI template update`, and labels `automerge` and `skip-changelog`.
- Skips the Copier update entirely when `.copier-answers.ci.yml` is missing.
- Fails before PR creation or branch push when Copier leaves merge conflicts in managed files.
- Writes a final workflow summary for both the PR and direct-push paths.

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

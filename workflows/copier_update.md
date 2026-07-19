# Copier Update

Run `copier update` and open or update a template-sync PR.

## Usage

```yaml
jobs:
  template-update:
    uses: athackst/ci/.github/workflows/copier_update.yml@main
    with:
      answers-file: .copier-answers.docs.yml
      pr-branch: ci/update-docs-template
      pr-title: "chore: update docs template"
      commit-message: "chore: apply docs template update"
    secrets:
      token: ${{ secrets.CI_BOT_TOKEN }}
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `dry-run` | (optional) Detect and report template changes while preserving repository state. | `false` |
| `pr-branch` | (optional) Branch name used for template updates. | `copier/update-template` |
| `pr-title` | (optional) Pull request title. | `chore: update Copier template` |
| `pr-labels` | (optional) Comma-separated list of labels to apply to the PR. | `""` |
| `commit-message` | (optional) Commit message for template updates. | `chore: apply Copier template update` |
| `checkout-ref` | (optional) Git ref to check out before applying template updates. | `""` |
| `template-ref` | (optional) Copier template ref to update from. Defaults to `checkout-ref`, then `HEAD`. | `""` |
| `answers-file` | (optional) Copier answers file to use for the update. | `.copier-answers.yml` |

## Secrets

| Name | Description |
| --- | --- |
| `token` | (optional) Token used for checkout, PR operations, failure issue maintenance, and label setup. Falls back to `${{ github.token }}`. |

## Outputs

| Name | Description |
| --- | --- |
| `changed` | Whether template changes were produced by Copier. |
| `changed-files` | Newline-delimited list of Copier-managed files changed by the update. |
| `branch` | Branch name used for the update PR; empty during dry runs. |
| `pr-url` | URL for the updater PR; empty during dry runs. |

## Permissions

- Dry runs use `contents: read`.
- Update runs use `contents: write`, `pull-requests: write`, `issues: write`, and `actions: write`.
- `actions: write` is needed when template updates modify `.github/workflows/*`.

## Advanced

- Skips the Copier update entirely when the configured answers file is missing.
- Detects and applies every change produced by Copier in the fresh checkout.
- Logs the managed-file status, diffstat, and diff from the `Detect changes` step and includes the changed file list in successful update summaries.
- `dry-run: true` reports changes and conflicts while preserving branches, pull requests, and failure issues.
- Fails before PR creation when Copier leaves merge conflicts, lists the conflicted files in the workflow summary, and prints index entries plus the diff in the log.
- Creates or updates one open failure issue with updater context and a local repro command if the workflow fails, then comments on and closes the issue after a later successful run.
- Writes a final workflow summary for PR and dry-run updates.

## Examples

Preview a template update:

```yaml
jobs:
  template-update:
    uses: athackst/ci/.github/workflows/copier_update.yml@main
    with:
      dry-run: true
      answers-file: .copier-answers.docs.yml
```

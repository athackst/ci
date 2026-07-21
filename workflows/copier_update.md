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
| `template-ref` | (optional) Copier template ref to update from. Copier selects the template version when omitted. | `""` |
| `answers-file` | (optional) Copier answers file to use for the update. | `.copier-answers.yml` |

## Secrets

| Name | Description |
| --- | --- |
| `token` | (optional) Token used for checkout and PR operations. Falls back to `${{ github.token }}`. |

## Outputs

| Name | Description |
| --- | --- |
| `changed` | Whether template changes were produced by Copier. |
| `changed-files` | Newline-delimited list of Copier-managed files changed by the update. |
| `pr-branch` | Branch name used for the update PR; empty when no PR is created. |
| `pr-url` | URL for the updater PR; empty when no PR is created. |

## Permissions

- Dry runs use `contents: read`.
- Update runs use `contents: write`, `pull-requests: write`, and `actions: write`.
- `actions: write` is needed when template updates modify `.github/workflows/*`.

## Advanced

- `checkout-ref` selects the destination state and `template-ref` selects the Copier template version applied to it.
- Requires the configured Copier answers file to exist.
- Detects and applies every change produced by Copier in the fresh checkout.
- Logs the managed-file status, diffstat, and diff and includes the changed file list in successful update summaries.
- `dry-run: true` reports changes and conflicts while preserving repository state.
- Fails before PR creation when Copier leaves merge conflicts, lists the conflicted files in the workflow summary, and prints the diff in the log.
- Writes a final workflow summary for PR and dry-run updates, including the Copier command for manual recovery after failures.

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

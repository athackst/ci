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
| `dry-run` | (optional) Detect and report template changes while preserving repository state. | `false` |
| `pr-branch` | (optional) Branch name used for template updates. | `ci/update-ci-template` |
| `checkout-ref` | (optional) Git ref to check out before applying template updates. | `""` |
| `template-ref` | (optional) CI template ref to apply. Uses `HEAD` by default. | `""` |
| `answers-file` | (optional) Copier answers file used for the CI template update. | `.copier-answers.ci.yml` |

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
- `actions: write` is needed in this environment when template updates modify `.github/workflows/*`.

## Advanced

- Wraps [`copier_update.yml`](copier_update.md) with CI-template defaults for existing consumers.
- `checkout-ref` selects the consumer state and `template-ref` selects the CI template version applied to it.
- Uses the configured Copier answers file for the CI template update.
- Detects and applies every change produced by Copier in the fresh checkout.
- Updater PRs use the title `chore: update CI template`, commit message `chore: apply CI template update`, and labels `automerge` and `skip-changelog`.
- `dry-run: true` reports changes and conflicts while preserving branches, pull requests, and failure issues.
- Skips the Copier update entirely when `.copier-answers.ci.yml` is missing.
- Fails before PR creation when Copier leaves merge conflicts.
- Writes a final workflow summary for PR and dry-run updates.

## Examples

Preview a CI template update:

```yaml
jobs:
  ci-update:
    uses: athackst/ci/.github/workflows/ci_updater.yml@main
    with:
      dry-run: true
```

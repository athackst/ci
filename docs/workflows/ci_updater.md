# CI Updater

Run `copier update` and open or update a template-sync PR.

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
| `pr-title` | (optional) Pull request title. | `chore: update CI template` |
| `commit-message` | (optional) Commit message for template updates. | `chore: apply CI template update` |
| `checkout-ref` | (optional) Git ref to check out before applying template updates. | `""` |

## Secrets

| Name | Description | Default |
| --- | --- | --- |
| `token` | (optional) Token used for checkout, push, PR operations, issue creation, and label setup. | `${{ github.token }}` |

## Outputs

| Name | Description |
| --- | --- |
| `changed` | Whether template changes were produced by Copier. |
| `branch` | Branch name used for the update, whether a PR was created or changes were pushed directly. |
| `pr-url` | URL for the updater PR, if one was created or updated. |

## Permissions

- Requires `contents: write`, `pull-requests: write`, `issues: write`, and `actions: write`.
- `actions: write` is needed in this environment when template updates modify `.github/workflows/*`.

## Advanced

- Skips the Copier update entirely when `.copier-answers.ci.yml` is missing.
- The `automerge` input is deprecated and currently has no effect; updater PRs are labeled automatically.
- Only changes under `.github/` and `.copier-answers.ci.yml` count toward the `changed` output, so other files do not open an update PR.
- Creates a failure issue with updater context and a local repro command if the workflow fails.
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

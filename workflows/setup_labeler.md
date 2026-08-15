# Setup Labeler

Create or update repository label metadata from the shared CI config.

## Usage

```yaml
jobs:
  setup-labels:
    uses: athackst/ci/.github/workflows/setup_labeler.yml@main
    secrets:
      token: ${{ secrets.CI_BOT_TOKEN }}
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `dry-run` | (optional) Report planned label changes without creating or updating labels. | `false` |

## Secrets

| Name | Description |
| --- | --- |
| `token` | (optional) Token used to create and update repository labels. Falls back to `${{ github.token }}`; dry runs only read existing labels. |

## Outputs

| Name | Description |
| --- | --- |
| `created-labels` | Comma-separated labels created. |
| `updated-labels` | Comma-separated labels updated. |
| `unchanged-labels` | Comma-separated labels already matching desired metadata. |
| `skipped-labels` | Comma-separated labels skipped because required metadata was missing. |

## Permissions

- Requires `issues: read` for dry runs and `issues: write` to create or update
  repository labels.
- Uses `contents: read` to check out the shared config.

## Advanced

- Always reads `.github/ci-config.yml`.
- Delegates label metadata updates to the `setup-labels` composite action.
- With `dry-run: true`, reports the planned changes without mutating repository labels.
- Writes a final workflow summary with created, updated, unchanged, and skipped labels.

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

## Secrets

| Name | Description |
| --- | --- |
| `token` | (optional) Token used to create and update repository labels. Falls back to `${{ github.token }}`. |

## Outputs

| Name | Description |
| --- | --- |
| `created-labels` | Comma-separated labels created. |
| `updated-labels` | Comma-separated labels updated. |
| `unchanged-labels` | Comma-separated labels already matching desired metadata. |
| `skipped-labels` | Comma-separated labels skipped because required metadata was missing. |

## Permissions

- Requires `issues: write` to create and update repository labels.
- Uses `contents: read` to check out the shared config.

## Advanced

- Always reads `.github/ci-config.yml`.
- Delegates label metadata updates to the `setup-labels` composite action.
- Writes a final workflow summary with created, updated, unchanged, and skipped labels.

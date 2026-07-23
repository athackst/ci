# Labeler

Apply pull request labels from the shared CI config.

## Usage

```yaml
jobs:
  pr-labels:
    uses: athackst/ci/.github/workflows/labeler.yml@main
    secrets:
      token: ${{ secrets.CI_BOT_TOKEN }}
```

## Secrets

| Name | Description |
| --- | --- |
| `token` | (optional) Token used to apply PR labels. Falls back to `${{ github.token }}`. |

## Permissions

- Requires `pull-requests: write` to add labels.
- Uses `contents: read` to check out the repository configuration.

## Advanced

- Always reads `.github/ci-config.yml` from the checked-out repository.
- Delegates the actual labeling logic to the `pr-labeler` composite action.
- Adds a workflow summary only when labels were actually added.

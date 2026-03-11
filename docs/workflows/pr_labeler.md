# PR Labeler

Apply pull request labels from the shared CI config.

## Usage

```yaml
jobs:
  pr-labels:
    uses: athackst/ci/.github/workflows/pr_labeler.yml@main
    secrets: inherit
```

## Permissions

- Requires `pull-requests: write` to add labels.
- Uses `contents: read` to resolve the shared config.

## Advanced

- Resolves `.github/ci-config.yml` first and tolerates missing config resolution with `continue-on-error`.
- Delegates the actual labeling logic to the `pr-labeler` composite action.
- Adds a workflow summary only when labels were actually added.

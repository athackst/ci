# Automerge

Enable GitHub auto-merge for pull requests labeled `automerge`.

## Usage

```yaml
jobs:
  automerge:
    uses: athackst/ci/.github/workflows/automerge.yml@main
    secrets:
      token: ${{ secrets.CI_BOT_TOKEN }}
```

## Secrets

| Name | Description | Default |
| --- | --- | --- |
| `token` | (optional) Token used for label inspection and enabling auto-merge. | `${{ github.token }}` |

## Permissions

- Requires `pull-requests: write` to enable auto-merge.
- `contents: read` is sufficient for the rest of the workflow.

## Advanced

- Only acts when the PR has an `automerge` label.
- Skips draft pull requests.
- Enables squash auto-merge with `gh pr merge --auto --squash`.

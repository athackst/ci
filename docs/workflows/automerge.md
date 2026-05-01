# Automerge

Handle pull requests labeled `automerge` using poll, native, or disabled mode.

## Usage

```yaml
jobs:
  automerge:
    uses: athackst/ci/.github/workflows/automerge.yml@main
    with:
      automerge-mode: poll
    secrets:
      token: ${{ secrets.CI_BOT_TOKEN }}
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `automerge-mode` | (optional) Merge strategy for PRs labeled `automerge`. Use `poll`, `native`, or `disabled`. | `poll` |

## Secrets

| Name | Description | Default |
| --- | --- | --- |
| `token` | (optional) Token used for label inspection and enabling auto-merge. | `${{ github.token }}` |

## Permissions

- Requires `pull-requests: write` to merge PRs directly or enable auto-merge.
- `contents: read` is sufficient for the rest of the workflow.

## Advanced

- Only acts when the PR has an `automerge` label.
- Skips draft pull requests.
- `poll` waits for required checks and then runs `gh pr merge --squash`.
- `native` enables GitHub auto-merge with `gh pr merge --auto --squash`.
- `disabled` leaves labeled PRs untouched.

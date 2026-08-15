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

| Name | Description |
| --- | --- |
| `token` | Token used to inspect labels, enable auto-merge, and merge pull requests. |

## Permissions

- Requires `contents: write` and `pull-requests: write` to merge PRs directly or enable auto-merge.
- Requires `checks: read` to poll required checks in `poll` mode.

## Advanced

- Callers should trigger on `labeled`, `unlabeled`, and `ready_for_review`, with
  per-PR concurrency and `cancel-in-progress: true`.
- Automerge requires a non-draft PR with the `automerge` label and a head branch
  in the target repository. The label is removed from fork PRs.
- `poll` waits for required checks, treats neutral checks as passing, and
  confirms the PR is still open and labeled immediately before merging.
- `native` enables GitHub auto-merge. Removing the label does not disable
  auto-merge that was enabled manually or by an earlier run.

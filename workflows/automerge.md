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
| `token` | (optional) Token used for label inspection and enabling auto-merge. Falls back to `${{ github.token }}`. |

## Permissions

- Requires `pull-requests: write` to merge PRs directly or enable auto-merge.
- Requires `checks: read` to poll required checks in `poll` mode.
- Uses `contents: read` for the rest of the workflow.

## Advanced

- Designed for callers triggered by open-PR `labeled`, `unlabeled`, and
  `ready_for_review` events. Label events for labels other than `automerge` are
  ignored.
- A `ready_for_review` event reconciles an existing `automerge` label, allowing
  a PR labeled while draft to begin automerge once it is ready.
- Only enables or performs automerge when the PR has an `automerge` label and
  its head branch is hosted in the target repository, not a fork.
- Removes the `automerge` label from fork PRs without altering native
  auto-merge state that was enabled manually.
- Skips draft pull requests.
- `poll` waits for required checks, confirms the `automerge` label is still
  present, and then runs `gh pr merge --squash`.
- `poll` treats neutral checks as passing.
- `native` enables GitHub auto-merge with `gh pr merge --auto --squash`.
- `native` disables GitHub auto-merge when the `automerge` label is removed;
  unrelated events without the label leave manually configured state alone.
- `disabled` performs no merge operation; the fork-label safety rule still
  applies.
- The workflow summary reports whether auto-merge was enabled or disabled, the
  PR was merged, or no automerge change was made.
- Callers should use per-PR concurrency that cancels an in-progress run only
  when the `automerge` label is removed. The final live-label check remains the
  merge authorization boundary in `poll` mode.

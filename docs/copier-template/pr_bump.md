# PR Bump

`pr_bump.yml` runs a repository-specific bump command after version metadata is
resolved.

## Generated When

Generated only when `bump_script_path` is set.

## Runs On

- `pull_request` when labels are added or removed

The job only runs for open, trusted same-repository pull requests and skips
Dependabot.

## Calls

```yaml
uses: athackst/ci/.github/workflows/bump.yml@main
```

See [`bump.yml`](../workflows/bump.md) for the reusable workflow contract.

## Permissions

- `contents: write` to push bump commits.
- `pull-requests: write` to update the bump PR comment.

## Behavior

- Passes `bump_script_path` to the reusable Bump workflow as `bump-script`.
- Resolves semantic version metadata from `.github/ci-config.yml`.
- Runs the configured bump command with version environment variables.
- Pushes any resulting commit back to the PR branch.
- Maintains a single PR comment describing bump results.

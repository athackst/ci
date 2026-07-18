# Release Draft

`release_draft.yml` creates or updates a draft GitHub release from merged pull
request metadata and the release template in `.github/ci-config.yml`.

## Generated When

Generated only when `do_releases` is enabled.

## Runs On

- Pushes to `main`
- Manual `workflow_dispatch`

## Calls

```yaml
uses: athackst/ci/.github/workflows/release_drafter.yml@main
```

See [`release_drafter.yml`](../workflows/release_drafter.md) for the reusable
workflow contract.

## Permissions

The release draft job needs:

- `contents: write` creates or updates draft releases.
- `pull-requests: read` resolves changelog and version metadata.

## Behavior

- Uses Release Drafter to resolve the version and changelog from `.github/ci-config.yml`.
- Creates or updates the repository's draft release after pushes to `main` or manual dispatches.
- Uses `secrets.CI_BOT_TOKEN` for release writes.

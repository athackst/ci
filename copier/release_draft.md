# Release Draft

`release_draft.yml` creates or updates a draft GitHub release from merged pull
request metadata and `.github/release_template.md`.

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

- `contents: write` to create or update draft releases.
- `pull-requests: read` to resolve changelog and version metadata.

## Behavior

- Creates or updates a draft release from resolved version and changelog data.
- Updates a draft release with the resolved tag when one exists.
- Otherwise updates the newest draft release containing the hidden release-draft marker.
- Uses `secrets.CI_BOT_TOKEN` for release writes.

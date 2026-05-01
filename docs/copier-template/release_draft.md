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

The `persist-draft-id` job needs:

- `actions: write` to persist `DRAFT_RELEASE_ID` as a repository variable.

## Behavior

- Passes `vars.DRAFT_RELEASE_ID` into the reusable Release Draft workflow.
- Creates or updates a draft release from resolved version and changelog data.
- Stores the resulting release ID in the `DRAFT_RELEASE_ID` repository variable
  for the next run.
- Uses `secrets.CI_BOT_TOKEN` for release and variable writes.

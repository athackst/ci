# CI Update

`ci_update.yml` keeps a consumer repository aligned with this CI template.

## Generated When

Always generated.

## Runs On

- Daily schedule at `0 15 * * *`
- Manual `workflow_dispatch`

## Calls

```yaml
uses: athackst/ci/.github/workflows/ci_updater.yml@main
```

See [`ci_updater.yml`](../workflows/ci_updater.md) for the reusable workflow
contract.

## Dependencies

```mermaid
flowchart LR
    template["Template workflow<br/>ci_update.yml"] --> updater["Reusable workflow<br/>ci_updater.yml"]
    updater --> copier["Reusable workflow<br/>copier_update.yml"]
    copier --> checkout["Action<br/>actions/checkout"]
    copier --> update["Composite action<br/>copier-update"]
    copier --> pull_request["Action<br/>peter-evans/create-pull-request"]

    classDef template fill:#e0f2fe,stroke:#0284c7
    classDef workflow fill:#ede9fe,stroke:#7c3aed
    classDef action fill:#ecfccb,stroke:#65a30d
    class template template
    class updater,copier workflow
    class checkout,update,pull_request action
```

## Permissions

- `contents: write` to commit template updates.
- `pull-requests: write` to open or update the template-sync PR.
- `actions: write` so updater PRs can modify `.github/workflows/*`.

## Behavior

- Runs `copier update` through the reusable CI Updater workflow.
- Opens or updates a PR from `ci/update-ci-template`.
- Labels updater PRs automatically for automerge and changelog skipping.
- Uses `secrets.CI_BOT_TOKEN` as the reusable workflow `token` secret.

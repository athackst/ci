# PR Labeler

`pr_labeler.yml` applies pull request labels from `.github/ci-config.yml`.

## Generated When

Always generated.

## Runs On

- `pull_request_target`

## Calls

```yaml
uses: athackst/ci/.github/workflows/labeler.yml@main
```

See [`labeler.yml`](../workflows/labeler.md) for the reusable workflow
contract.

## Dependencies

```mermaid
flowchart LR
    template["Template workflow<br/>pr_labeler.yml"] --> labeler["Reusable workflow<br/>labeler.yml"]
    labeler --> checkout["Action<br/>actions/checkout"]
    labeler --> wrapper["Composite action<br/>pr-labeler"]
    wrapper --> upstream["Action<br/>actions/labeler"]

    classDef template fill:#e0f2fe,stroke:#0284c7
    classDef workflow fill:#ede9fe,stroke:#7c3aed
    classDef action fill:#ecfccb,stroke:#65a30d
    class template template
    class labeler workflow
    class checkout,wrapper,upstream action
```

## Permissions

- `contents: read` to check out `.github/ci-config.yml`.
- `pull-requests: write` to apply PR labels.

## Behavior

- Uses the shared CI config as the labeler source.
- Routes secret-requiring label writes through `pull_request_target`.
- Uses `secrets.CI_BOT_TOKEN` as the reusable workflow `token` secret.
- The reusable workflow checks out the repository configuration and delegates matching to the
  [`pr-labeler`](../actions/pr-labeler/README.md) composite action.

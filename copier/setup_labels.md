# Setup Labels

`setup_labels.yml` creates or updates repository label metadata from
`.github/ci-config.yml`.

## Generated When

Always generated.

## Runs On

- Pushes to `main` that change `.github/ci-config.yml`
- Manual `workflow_dispatch`

## Calls

```yaml
uses: athackst/ci/.github/workflows/setup_labeler.yml@main
```

See [`setup_labeler.yml`](../workflows/setup_labeler.md) for the reusable
workflow contract.

## Dependencies

```mermaid
flowchart LR
    template["Template workflow<br/>setup_labels.yml"] --> setup["Reusable workflow<br/>setup_labeler.yml"]
    setup --> checkout["Action<br/>actions/checkout"]
    setup --> setup_labels["Composite action<br/>setup-labels"]

    classDef template fill:#e0f2fe,stroke:#0284c7
    classDef workflow fill:#ede9fe,stroke:#7c3aed
    classDef action fill:#ecfccb,stroke:#65a30d
    class template template
    class setup workflow
    class checkout,setup_labels action
```

## Permissions

- `contents: read` to check out `.github/ci-config.yml`.
- `issues: write` to create and update repository labels.

## Behavior

- Uses `secrets.CI_BOT_TOKEN` as the reusable workflow `token` secret.
- Reads `.github/ci-config.yml`.
- Creates, updates, skips, or leaves labels unchanged based on label metadata
  through the [`setup-labels`](../actions/setup-labels/README.md) composite
  action.

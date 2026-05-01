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
uses: athackst/ci/actions/setup-labels@main
```

See [`setup-labels`](../actions/setup-labels/README.md) for the composite
action contract.

## Permissions

The generated workflow does not declare an explicit `permissions` block. It
uses `secrets.CI_BOT_TOKEN` when available, falling back to `github.token`.

The token must be able to create and update repository labels. `issues: write`
is typically sufficient for that operation.

## Behavior

- Checks out the repository.
- Reads `.github/ci-config.yml`.
- Creates, updates, skips, or leaves labels unchanged based on label metadata.

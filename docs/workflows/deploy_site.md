# Deploy Site

Deploy a built site artifact either to GitHub Pages or to a versioned branch.

## Usage

```yaml
jobs:
  deploy-site:
    uses: athackst/ci/.github/workflows/deploy_site.yml@main
    with:
      type: action
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `type` | (optional) Deployment mode. Use `action` for GitHub Pages artifact deploys or `branch` for versioned branch publishing. | `action` |
| `enablement` | (optional) Try to enable GitHub Pages for the repository before deploying. | `false` |
| `version` | (optional) Version identifier to publish, for example `dev` or `1.2.3`. Required for `type: branch`. | `""` |
| `artifact-name` | (optional) Artifact name containing the built site content. | `github-pages` |
| `branch` | (optional) Deployment branch for `type: branch`. Uses the action default when empty. | `""` |
| `dry-run` | (optional) Disable the publish step while still running workflow setup and artifact preparation. | `false` |

## Secrets

| Name | Description | Required |
| --- | --- | --- |
| `token` | Token override for `actions/configure-pages` when `enablement: true`. | `false` |

## Permissions

- Requires `contents: write`, `pages: write`, and `id-token: write` in the caller job.

## Advanced

- `type: action` uses `actions/deploy-pages` and is intended for unversioned GitHub Pages deploys.
- `type: branch` extracts the built artifact and publishes it with `PrimerPages/versite`.
- On release-triggered versioned publishes, the workflow adds the `latest` alias automatically.
- `dry-run: true` skips the final publish step for both deployment modes.

## Examples

Deploy the standard Pages artifact:

```yaml
jobs:
  deploy-site:
    permissions:
      contents: write
      pages: write
      id-token: write
    uses: athackst/ci/.github/workflows/deploy_site.yml@main
```

Publish versioned docs to a branch:

```yaml
jobs:
  deploy-site:
    permissions:
      contents: write
      pages: write
      id-token: write
    uses: athackst/ci/.github/workflows/deploy_site.yml@main
    with:
      type: branch
      version: dev
      branch: gh-pages
```

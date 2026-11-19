# Deploy Site

Deploy a built site artifact through GitHub Pages Actions, preserving version history in a branch when a version is supplied.

## Usage

```yaml
jobs:
  deploy-site:
    permissions:
      contents: write
      pages: write
      id-token: write
    uses: athackst/ci/.github/workflows/deploy_site.yml@main
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `enablement` | (optional) Try to enable GitHub Pages for the repository before deploying. | `false` |
| `version` | (optional) Version identifier to publish, for example `dev` or `1.2.3`. When empty, deploys the original artifact directly. | `""` |
| `artifact-name` | (optional) Artifact name containing the built site content. | `github-pages` |
| `branch` | (optional) Branch storing published versions. | `gh-pages` |
| `dry-run` | (optional) Prepare version updates and artifacts without pushing or deploying. | `false` |

## Secrets

| Name | Description |
| --- | --- |
| `token` | (optional) Token override for `actions/configure-pages` when `enablement: true`. Falls back to `${{ github.token }}`. |

## Permissions

- Requires `contents: write`, `pages: write`, and `id-token: write` in the caller job.
- When `enablement: true` uses a fine-grained token override, that token needs `Pages: Read and write` and `Administration: Read and write` to create or configure the Pages site.

## Advanced

- Version preparation downloads the built-site artifact and uses versite to update the version branch, including older versions, aliases, redirects, and `versions.json`.
- The complete updated branch is packaged and deployed through GitHub Pages Actions. Packaging exports the exact local commit produced by versite, without another fetch.
- Preparation needs only repository contents permissions; Pages configuration and deployment run in the deployment job.
- Set the repository Pages source to **GitHub Actions**. Existing branch-configured sites can also accept Actions deployments when the workflow runs from the configured source branch or the deployment environment protection rules permit its ref.
- Builds must use the base URL for their version directory; deployment does not rewrite site URLs.
- Production deployments are serialized per repository, with up to 100 pending runs retained instead of replacing queued releases. Dry runs use separate, run-specific concurrency groups so they cannot displace production deployments.
- On release-triggered versioned publishes, the workflow adds the `latest` alias automatically.
- `dry-run: true` prepares version updates locally without pushing or deploying, and uploads the complete site for inspection under `versioned-<artifact-name>`. Unversioned dry runs skip deployment.

## Examples

Publish versioned docs through GitHub Pages Actions while retaining `gh-pages` history:

```yaml
jobs:
  deploy-site:
    permissions:
      contents: write
      pages: write
      id-token: write
    uses: athackst/ci/.github/workflows/deploy_site.yml@main
    with:
      version: dev
```

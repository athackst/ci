# MkDocs Site

Build a MkDocs site, run HTMLProofer checks, and optionally deploy to GitHub Pages or publish versioned docs.

## Usage

```yaml
jobs:
  site:
    uses: athackst/ci/.github/workflows/mkdocs_site.yml@main
    with:
      pages: true
    secrets:
      token: ${{ secrets.CI_BOT_TOKEN }}
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `pages` | (optional) Deploy to GitHub Pages after build and test. | `true` |
| `enablement` | (optional) Try to enable Pages for the repository if needed. | `false` |
| `htmlproofer-ignore-urls` | (optional) Newline-delimited URLs or regexes for HTMLProofer to ignore. | `""` |
| `artifact-name` | (optional) Artifact name for the built site. | `github-pages` |
| `version` | (optional) Version alias string for versioned docs publishing. | `""` |
| `release-tag` | (optional) Release tag used for versioned release docs publishing. | `""` |

## Secrets

| Name | Description | Default |
| --- | --- | --- |
| `token` | (optional) Token override used by `configure-pages`. | `${{ github.token }}` |

## Permissions

- Build/test only needs read access.
- Deployment needs `contents: write`, `pages: write`, and `id-token: write` in the caller job.
- If `enablement: true`, the token must be able to enable Pages for the repository.

## Advanced

- Uses the bundled `mkdocs-config` action before build and again before versioned publish.
- Reuses [`htmlproofer_site.yml`](./htmlproofer_site.md) for post-build link checking.
- When `version` is empty, deploys the artifact to Pages only on `main`.
- When `version` is non-empty, publishes versioned docs with `athackst/mkdocs-simple-plugin`.
- `release-tag` is intended for release-mode version publishing, for example `v1.2.3 latest`.

## Examples

Publish versioned docs:

```yaml
jobs:
  site:
    uses: athackst/ci/.github/workflows/mkdocs_site.yml@main
    with:
      pages: true
      version: dev
    secrets:
      token: ${{ secrets.CI_BOT_TOKEN }}
```

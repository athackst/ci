# Jekyll Site

Build a Jekyll site, run HTMLProofer checks, and optionally deploy to GitHub Pages.

## Usage

```yaml
jobs:
  site:
    uses: athackst/ci/.github/workflows/jekyll_site.yml@main
    with:
      pages: true
      path: docs
    secrets:
      token: ${{ secrets.CI_BOT_TOKEN }}
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `pages` | (optional) Deploy to GitHub Pages after build and test. | `true` |
| `enablement` | (optional) Try to enable Pages for the repository if needed. | `false` |
| `htmlproofer-ignore-urls` | (optional) Newline-delimited URLs or regexes for HTMLProofer to ignore. | `""` |
| `path` | (optional) Path to the Jekyll project directory. | `.` |
| `artifact-name` | (optional) Artifact name for the built site. | `github-pages` |

## Secrets

| Name | Description | Default |
| --- | --- | --- |
| `token` | (optional) Token override used by `configure-pages`. | `${{ github.token }}` |

## Permissions

- Build/test only needs read access.
- Deployment needs `contents: write`, `pages: write`, and `id-token: write` in the caller job.
- If `enablement: true`, the token must be able to enable Pages for the repository.

## Advanced

- Builds the site from the configured `path` with Bundler cache enabled.
- Reuses [`htmlproofer_site.yml`](./htmlproofer_site.md) for post-build link checking.
- Deploys only when `pages: true` and the ref is `refs/heads/main`.
- Exposes `host` and `base-path` internally so HTMLProofer can validate Pages-style links correctly.

## Examples

Testing on a PR:

site.yml is no longer automatically tested on PRs.  If you want to test on a PR add the following to your test workflow

```yaml
jobs:
  test-site:
    if: ${{ github.event_name == 'pull_request' }}
    permissions:
      contents: read
    uses: athackst/ci/.github/workflows/jekyll_site.yml@main
    with:
      pages: false
    secrets: inherit
```

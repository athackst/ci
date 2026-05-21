# Site

`site.yml` builds and optionally deploys documentation sites.

## Generated When

Generated when `site_generator` is `mkdocs` or `jekyll`.

No site workflow is generated when `site_generator` is `none`.

## Runs On

- Pushes to `main`
- Pull requests
- Release `published` events for the MkDocs release job

## Calls

For MkDocs:

```yaml
uses: athackst/ci/.github/workflows/mkdocs_site.yml@main
```

See [`mkdocs_site.yml`](../workflows/mkdocs_site.md) for the reusable workflow
contract.

For Jekyll:

```yaml
uses: athackst/ci/.github/workflows/jekyll_site.yml@main
```

See [`jekyll_site.yml`](../workflows/jekyll_site.md) for the reusable workflow
contract.

## Permissions

- `build-site`: `contents: read`
- `test-site`: `contents: read`
- `deploy-site`: `contents: write`, `pages: write`, `id-token: write`

## Behavior

- On pull requests, builds the configured site and runs HTMLProofer without deploying.
- On `main` pushes, builds and deploys the configured site.
- `build-site` is responsible for building the site artifact and exposing the site metadata used by `test-site` and `deploy-site`.
- `test-site` runs HTMLProofer against the built artifact and reports link failures without blocking deployment.
- `deploy-site` handles the publish step:
  - non-versioned sites deploy the built artifact with GitHub Pages actions
  - versioned MkDocs sites publish with `PrimerPages/versite` via branch
  - `dry-run` disables the publish step for either deployment mode

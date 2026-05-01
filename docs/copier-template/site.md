# Site

`site.yml` builds and optionally deploys documentation sites.

## Generated When

Generated when `site_generator` is `mkdocs` or `jekyll`.

No site workflow is generated when `site_generator` is `none`.

## Runs On

- Pushes to `main`
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

- `contents: write`
- `pages: write`
- `id-token: write`

## Behavior

- On `main` pushes, builds and deploys the configured site.
- For MkDocs, release publishes run a second job through `mkdocs_site.yml`.
- When `do_releases` is enabled for MkDocs:
  - `main` publishes the `dev` version.
  - release publishes publish `latest` with `release-tag` set to the release tag.
- Jekyll site workflows do not publish versioned docs.

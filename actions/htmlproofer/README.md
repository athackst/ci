# HTMLProofer Action

Runs HTMLProofer against a built site artifact.

This action:

1. Downloads a site artifact (default name: `github-pages`)
2. Extracts it to `_site`
3. Adds default ignore URL patterns for commonly flaky external services
4. Runs `athackst/htmlproofer-action`

## Usage

```yaml
- name: Test site with HTMLProofer
  uses: athackst/ci/actions/htmlproofer@main
  with:
    host: myuser.github.io
    base-path: /my-repo
    artifact-name: github-pages
    ignore-urls: |
      /^https:\/\/example\.com$/
```

## Inputs

- `host` (optional): Site host used by HTMLProofer URL swap logic.
  - Example: `myuser.github.io`
- `base-path` (optional): Site base path.
  - Example: `/my-repo`
- `artifact-name` (optional, default: `github-pages`): Artifact to download.
- `ignore-urls` (optional): Newline-delimited URLs/regexes to ignore.

## Default ignored URL patterns

These are always appended before your custom `ignore-urls`:

- Twitter/X domains
- Google Fonts APIs/CDN

This helps avoid noisy external-link failures that are unrelated to site correctness.

## Artifact expectations

The action supports:

- `artifact.tar` directly at `./artifact/artifact.tar`
- any `*.tar` up to depth 2 under `./artifact`
- already-extracted artifact contents

## Troubleshooting

- If extraction fails, check the uploaded artifact structure from your site build workflow.
- If links fail unexpectedly, print `_site` contents and verify `host`/`base-path` values.
- If you need stricter checks, reduce `ignore-urls` in the caller workflow.

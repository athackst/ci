# HTMLProofer Site

Test a built site artifact with HTMLProofer.

## Usage

```yaml
jobs:
  test-site:
    uses: athackst/ci/.github/workflows/htmlproofer_site.yml@main
    with:
      artifact-name: github-pages
      host: my-org.github.io
      base-path: /my-repo
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `host` | (optional) Site host used for htmlproofer URL swapping. | `""` |
| `base-path` | (optional) Site base path used for htmlproofer URL swapping. | `""` |
| `htmlproofer-ignore-urls` | (optional) Newline-delimited URLs or regexes to ignore. | `""` |
| `artifact-name` | (optional) Artifact name containing built site content. | `github-pages` |

## Permissions

- Requires only `contents: read`.

## Advanced

- Accepts either the Pages artifact tarball layout or a plain uploaded site directory.
- Adds a built-in ignore list for common external assets such as Twitter/X and Google Fonts.
- Caches HTMLProofer output under `tmp/.htmlproofer`.
- Always tests the extracted site under `_site/`.

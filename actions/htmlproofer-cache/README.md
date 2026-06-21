# HTMLProofer Cache

Run HTMLProofer with shared cache restore and save steps.

## Usage

```yaml
- name: Test site with HTMLProofer
  uses: athackst/ci/actions/htmlproofer-cache@main
  with:
    host: my-org.github.io
    base-path: /my-repo
    ignore-urls: ${{ steps.options.outputs.ignore-urls }}
    swap-urls: ${{ steps.options.outputs.swap-urls }}
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `host` | (optional) Site host used for htmlproofer URL swapping. | `""` |
| `base-path` | (optional) Site base path used for htmlproofer URL swapping. | `""` |
| `ignore-urls` | (optional) Newline-delimited URLs or regexes to ignore. | `""` |
| `swap-urls` | (optional) Newline-delimited URL rewrite rules for HTMLProofer. | `""` |

## Advanced

- Restores and saves the shared `tmp/.htmlproofer` cache around the HTMLProofer run.
- Leaves ignore URL and swap URL construction to the calling workflow.

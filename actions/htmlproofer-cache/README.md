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

- Restores the newest shared `tmp/.htmlproofer` cache and saves refreshed results under a unique workflow-run key.
- Rechecks cached links weekly, limits HTTP concurrency to two requests, retries failures three times, and skips external fragment validation.
- Leaves ignore URL and swap URL construction to the calling workflow.

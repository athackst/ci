# Release Draft

Resolve version metadata, build a changelog, and create or update a draft GitHub release.

## Usage

```yaml
jobs:
  release:
    uses: athackst/ci/.github/workflows/release_drafter.yml@main
    secrets:
      token: ${{ secrets.CI_BOT_TOKEN }}
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `configuration-path` | (optional) Path to the release-drafter style config file. | `.github/ci-config.yml` |
| `name` | (optional) Explicit release name override. | `""` |
| `tag-name` | (optional) Explicit release tag name override. | `""` |
| `release-match-pattern` | (optional) Regex used to select the draft release to update by tag name. | `^v[0-9.]+$` |

## Secrets

| Name | Description | Default |
| --- | --- | --- |
| `token` | (optional) Token used to create or update the draft release. | `${{ github.token }}` |

## Outputs

| Name | Description |
| --- | --- |
| `id` | Draft release ID. |
| `name` | Draft release name. |
| `tag-name` | Draft release tag name. |
| `html-url` | Draft release HTML URL. |
| `upload-url` | Draft release upload URL. |
| `resolved-version` | Resolved semantic version used for defaults. |
| `changelog` | Generated changelog markdown body. |

## Permissions

- Requires `contents: write` to create or update releases.
- Requires `pull-requests: read` for version/changelog resolution.

## Advanced

- Resolves config first with `resolve-config`, then feeds the same config into version resolution and changelog generation.
- Uses the resolved version and generated changelog as the default release name, tag, and body inputs.
- Supports caller overrides for release `name`, `tag-name`, and draft matching pattern.
- Checks out tags with full history so semantic version resolution can compare against prior tags.

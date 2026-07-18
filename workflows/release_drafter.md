# Release Draft

Create or update a draft GitHub release from merged pull requests.

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
| `dry-run` | (optional) Preview the generated release draft while preserving repository releases. | `false` |

## Secrets

| Name | Description |
| --- | --- |
| `token` | (optional) Token used to create or update the draft release. Falls back to `${{ github.token }}`. |

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

- `contents: read` supports dry-run previews; live runs use `contents: write` to create or update releases.
- `pull-requests: read` resolves version and changelog metadata.

## Advanced

- Uses `release-drafter/release-drafter@v7` with the repository configuration in `.github/ci-config.yml`.
- Uses the resolved version and generated changelog for the release name, tag, and body.
- Supports caller overrides for release `name` and `tag-name`.
- `dry-run: true` resolves the version and renders the changelog while preserving repository releases.
- Dry runs provide `resolved-version` and `changelog`; live runs also provide the release resource outputs.

# Release Draft

Create or update a draft GitHub release from a release-drafter style config, a resolved version, and changelog content.

## Usage

```yaml
- name: Create draft release
  id: release_draft
  uses: athackst/ci/actions/release-draft@main
  with:
    token: ${{ github.token }}
    resolved-version: ${{ steps.version.outputs.resolved-version }}
    changelog: ${{ steps.changelog.outputs.changelog }}
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `token` | GitHub token used to draft the release. | None |
| `configuration-path` | (optional) Path to a release-drafter style config file. | Bundled `release-drafter.yml` |
| `changelog` | Changelog content interpolated into the release body template. | None |
| `resolved-version` | Version interpolated into the release name and tag templates. | None |
| `name` | (optional) Release name override. | Rendered from config |
| `tag-name` | (optional) Release tag name override. | Rendered from config |
| `draft-release-id` | (optional) Existing draft release ID to update directly before falling back to create. | `""` |
| `reuse-existing-draft` | (optional) Update an existing draft when no release ID or matching tag is found. | `true` |

## Outputs

| Name | Description |
| --- | --- |
| `id` | The release ID. |
| `name` | The release name. |
| `tag-name` | The release tag name. |
| `html-url` | The HTML URL for the release. |
| `upload-url` | The upload URL for release assets. |

## Permissions

- Requires a token that can create and update releases. `contents: write` is typically sufficient.

## Advanced

- Uses the bundled `release-drafter.yml` when `configuration-path` is not set.
- Supports `name-template`, `tag-template`, and `template`, plus `template-file` for loading the release body from a file.
- Template interpolation supports `$RESOLVED_VERSION`, `$VERSION`, `$CHANGES`, and `$CHANGELOG`.
- When `draft-release-id` is provided, the action updates that release only when it is still a draft; otherwise it is ignored.
- Otherwise, the action updates a draft release with the resolved tag when one exists.
- If no matching tag is found and `reuse-existing-draft` is `true`, the action updates the newest existing draft release.
- If no release ID, matching tag, or reusable draft is available, the action creates a new draft release.

## Examples

Use a repository-specific release config:

```yaml
- name: Create draft release
  uses: athackst/ci/actions/release-draft@main
  with:
    token: ${{ secrets.CI_BOT_TOKEN }}
    configuration-path: .github/release-drafter.yml
    resolved-version: ${{ steps.version.outputs.resolved-version }}
    changelog: ${{ steps.changelog.outputs.changelog }}
```

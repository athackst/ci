# Version Resolver

Resolve the changelog base ref and next semantic version from merged pull request labels.

## Usage

```yaml
- name: Resolve version metadata
  id: version
  uses: athackst/ci/actions/version-resolver@main
  with:
    gh-token: ${{ github.token }}
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `configuration-path` | (optional) Path to the version resolver config. | Bundled `versions.yml` |
| `repo` | (optional) Repository in `owner/repo` format used for pull request lookup. | `${{ github.repository }}` |
| `gh-token` | (optional) GitHub token used for API lookup. | `${{ github.token }}` |
| `pr-info-path` | (optional) Output file path for resolver PR info JSON data. | `${{ runner.temp }}/version-resolver-pr-info.json` |

## Outputs

| Name | Description |
| --- | --- |
| `from-ref` | Resolved changelog base reference. |
| `resolved-version` | Resolved semantic version. |
| `major-version` | Resolved major version component. |
| `minor-version` | Resolved minor version component. |
| `patch-version` | Resolved patch version component. |
| `pr-info-path` | Path to the resolver PR info JSON data file. |

## Permissions

- Requires a token that can read repository contents and pull request metadata. `contents: read` and `pull-requests: read` are typically sufficient.

## Advanced

- Uses the latest reachable `vX.Y.Z` tag as `from-ref`; if no semantic version tag exists, it falls back to the repository's first commit.
- Pull request discovery prefers the compare API and falls back to paginated closed pull request listing when needed.
- Any configured `major` label wins over `minor`, and any configured `minor` label wins over `patch`.
- If no merged PR labels match configured `major` or `minor` labels, the version defaults to a patch bump.
- The action writes a compact PR metadata JSON file that can be consumed directly by `actions/changelog`.

## Examples

Use a repository-specific version config:

```yaml
- name: Resolve version metadata
  id: version
  uses: athackst/ci/actions/version-resolver@main
  with:
    configuration-path: .github/versions.yml
    gh-token: ${{ secrets.CI_BOT_TOKEN }}
```

# Setup Labels

Create or update repository label metadata from a label configuration file.

## Usage

```yaml
- name: Setup labels
  id: labels
  uses: athackst/ci/actions/setup-labels@main
  with:
    github-token: ${{ github.token }}
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `github-token` | (optional) GitHub token with permissions to manage repository labels. | `${{ github.token }}` |
| `repo` | (optional) Repository in `owner/repo` format where labels should be managed. | `${{ github.repository }}` |
| `configuration-path` | (optional) Path to the label configuration file. | Bundled `../pr-labeler/labeler.yml` |
| `dry-run` | (optional) Report planned changes without creating or updating labels. | `false` |

## Outputs

| Name | Description |
| --- | --- |
| `created-labels` | Comma-separated labels created. |
| `updated-labels` | Comma-separated labels updated. |
| `unchanged-labels` | Comma-separated labels already matching the desired metadata. |
| `skipped-labels` | Comma-separated labels skipped because they did not define usable metadata for label setup. |

## Permissions

- Requires a token that can create and update repository labels. `issues: write` is typically sufficient; dry runs only need read access to labels.

## Advanced

- Uses the bundled PR labeler config when `configuration-path` is not set.
- If a custom config path is missing, the action falls back to the bundled config.
- The action validates the config before calling the GitHub API.
- Labels with neither `description` nor `color` are skipped quietly.
- If `description` is missing, the label is skipped.
- If `color` is missing, the action uses the default color `808080`.
- Outputs are written before the step fails, so skipped and partial results remain available on error.
- Existing labels are matched case-insensitively before deciding whether to create, update, or leave them unchanged.
- With `dry-run: true`, the action reads existing labels and reports the create/update plan without mutating the repository.

## Examples

Use a repository-specific label config:

```yaml
- name: Setup labels
  uses: athackst/ci/actions/setup-labels@main
  with:
    github-token: ${{ secrets.CI_BOT_TOKEN }}
    configuration-path: .github/ci-config.yml
```

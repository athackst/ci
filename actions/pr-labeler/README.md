# PR Labeler

Apply pull request labels using a centralized labeler configuration.

## Usage

```yaml
- name: Label pull request
  id: labeler
  uses: athackst/ci/actions/pr-labeler@main
  with:
    github_token: ${{ github.token }}
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `github_token` | (optional) GitHub token used to read pull requests and add labels. | `${{ github.token }}` |
| `configuration-path` | (optional) Path to the labeler configuration file. | Bundled `labeler.yml` |

## Outputs

| Name | Description |
| --- | --- |
| `new-labels` | Comma-separated labels added by the action. |

## Permissions

- Requires a token that can read the pull request and add labels to it.

## Advanced

- Uses the bundled labeler config when `configuration-path` is not set.
- If a custom `configuration-path` is missing, the action falls back to the bundled config.
- Config is schema-validated and flattened before calling `actions/labeler`.
- Intended for pull request contexts where labels can be applied.

## Examples

Use a repository-specific labeler config:

```yaml
- name: Label pull request
  uses: athackst/ci/actions/pr-labeler@main
  with:
    github_token: ${{ secrets.CI_BOT_TOKEN }}
    configuration-path: .github/ci-config.yml
```


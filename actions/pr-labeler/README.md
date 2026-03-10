# PR Labeler

Apply pull request labels using a centralized labeler configuration.

## Usage

```yaml
- name: Label pull request
  id: labeler
  uses: athackst/ci/actions/pr-labeler@main
  with:
    github_token: ${{ github.token }}
    configuration-path: .github/ci-config.yml
```

## Inputs

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `github_token` | `string` | (optional) GitHub token used to read pull requests and add labels. | `${{ github.token }}` |
| `configuration-path` | `string` | (optional) Path to the labeler configuration file. | Bundled `labeler.yml` |

## Outputs

| Name | Description |
| --- | --- |
| `new-labels` | Comma-separated labels added by the action. |

## Permissions

- Requires a token with permission to write pull request labels.

## Advanced

- Uses the bundled labeler config by default.
- Use `configuration-path` to override the bundled labeling rules.
- Intended for pull request contexts where labels can be added.

## Examples

Use the bundled labeler config:

```yaml
- name: Label pull request
  uses: athackst/ci/actions/pr-labeler@main
```

Minimal custom config:

```yaml
labels:
  documentation:
    - changed-files:
        - any-glob-to-any-file: "**/*.md"
    - color: "65a30d"
    - description: "Change to documentation"
```

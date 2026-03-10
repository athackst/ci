# Changelog Action

Build release changelog markdown from PR metadata and changelog configuration.

## Usage

```yaml
- name: Resolve version metadata
  id: version
  uses: athackst/ci/actions/version-resolver@main
  with:
    gh-token: ${{ github.token }}

- name: Build changelog
  id: changelog
  uses: athackst/ci/actions/changelog@main
  with:
    pr-info-path: ${{ steps.version.outputs.pr-info-path }}
    # optional:
    # configuration-path: .github/changelog.yml

- name: Show changelog
  shell: bash
  run: |
    echo "${{ steps.changelog.outputs.changelog }}"
```

## Inputs

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `pr-info-path` | `string` | Path to PR metadata JSON. | None |
| `configuration-path` | `string` | (optional) Path to changelog config YAML. | Bundled `changelog.yml` |

## Outputs

| Name | Description |
| --- | --- |
| `changelog` | Category-grouped changelog markdown. |
| `pull-requests` | Comma-separated PR numbers included in the changelog output. |

## Advanced

- The action reads PRs from either `pr_info.pull_requests` or top-level `pull_requests`.
- Category matching is ordered and first-match-wins. A PR is included at most once.
- PRs with no matching category are rendered under `## Miscellaneous`.
- PRs with any label listed in `exclude-labels` are skipped.
- `label` and `labels` are both supported in `changelog.yml`. `label` may be a string or list.
- If `collapse-after` is set and the matched PR count exceeds it, that category is wrapped in a `<details>` block.
- If `number` and `html_url` are present, a PR entry is rendered as a markdown link.
- If only `number` is present, a PR entry is rendered as plain `#123` text.
- If `title` is missing, the action still renders a list item.
- Only non-excluded PRs with a `number` are included in the `pull-requests` output.

## Examples

Custom `changelog.yml`:

```yaml
categories:
  - title: ':rocket: New'
    label: 'feature'
  - title: ':bug: Bug Fixes'
    labels: ['bug', 'fix']
  - title: 'Dependency Updates'
    label: 'dependencies'
    collapse-after: 3
exclude-labels:
  - 'skip-changelog'
```

Minimal `pr_info` payload:

```json
{
  "pr_info": {
    "pull_requests": [
      {
        "number": 42,
        "title": "Fix edge case in parser",
        "html_url": "https://github.com/org/repo/pull/42",
        "labels": ["bug", "maintenance"]
      }
    ]
  }
}
```

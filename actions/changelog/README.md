# Changelog Action

Builds release changelog markdown from:

- a `pr_info` JSON file (typically from `actions/version-resolver`)
- a changelog config YAML file

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

- `pr-info-path` (required): Path to PR metadata JSON.
- `configuration-path` (optional): Path to changelog config YAML.
  - default: `actions/changelog/changelog.yml` from this action.

## Outputs

- `changelog`: Category-grouped changelog content.
- `pull-requests`: Comma-separated PR numbers included in changelog.

## Config Format

Example (`changelog.yml`):

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

Notes:

- `label` and `labels` are both supported.
- `collapse-after` is optional per category.
  - If set, and matched PR count is greater than this value, that category is wrapped in a `<details>` block.
- Category matching is ordered and first-match-wins.
  - A PR appears at most once.
- PRs with no category match go to `### Miscellaneous`.
- PRs with any `exclude-labels` label are skipped.

## Expected `pr_info` JSON

The action expects a top-level object with either:

- `pr_info.pull_requests`
- or `pull_requests`

Each pull request item should include:

- `number` (int, optional but recommended)
- `title` (string)
- `html_url` (string, optional)
- `labels` (list of strings or list of `{name: ...}` objects)

Minimal example:

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

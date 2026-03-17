# List Repos

List repositories for a GitHub user and write a filtered JSON array of repository metadata to a file.

## Usage

```yaml
- name: List repositories
  id: repos
  uses: athackst/ci/actions/list-repos@main
  with:
    github-token: ${{ github.token }}
    user: octocat
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `github-token` | (optional) GitHub token used for GitHub API access. | `${{ github.token }}` |
| `user` | (optional) GitHub username whose repositories should be listed. | `${{ github.repository_owner }}` |
| `public` | (optional) Include public repositories when `true`. Set to `false` to exclude them. | `"true"` |
| `private` | (optional) Include private repositories when `true`. Set to `false` to exclude them. | `"true"` |
| `fork` | (optional) Include fork repositories when `true`. Set to `false` to exclude them. | `"true"` |
| `archived` | (optional) Include archived repositories when `true`. Set to `false` to exclude them. | `"true"` |
| `filter-paths` | (optional) Newline-delimited repository paths. Repositories are returned only if any listed path exists. | `""` |
| `output-path` | (optional) Path to write the repository JSON file. | `.github/repositories.json` |

## Outputs

| Name | Description |
| --- | --- |
| `repository-file` | Path to a JSON file containing matching repository metadata objects. |

## Permissions

- Public repository listing works with the default token.
- Listing private repositories requires a token that can read the target user's private repositories.

## Advanced

- Supports GitHub users only and fails for organizations.
- When `private: true`, the action uses authenticated repo listing so private repositories can be included; with GitHub App tokens it falls back to installation repositories.
- `public`, `private`, `fork`, and `archived` are inclusive toggles. The default `true` value includes that category, and `false` removes it from the results.
- `filter-paths` checks each listed path with the GitHub contents API and returns the repository only when any path exists.
- `repository-file` is useful when later workflow steps should read repo data without echoing repository names to the logs.
- For local usage, call `python3 actions/list-repos/list_repos.py --user <name> ...` directly.

## Examples

List only archived repositories:

```yaml
- name: List archived repositories
  id: archived
  uses: athackst/ci/actions/list-repos@main
  with:
    github-token: ${{ github.token }}
    user: octocat
    public: false
    private: false
    fork: false
    archived: true
```

List both public and private repositories that are not forks or archives:

```yaml
- name: List active repositories
  id: active
  uses: athackst/ci/actions/list-repos@main
  with:
    github-token: ${{ github.token }}
    user: octocat
    fork: false
    archived: false
```

List repositories that contain a Copier answers file:

```yaml
- name: List template-managed repositories
  id: managed
  uses: athackst/ci/actions/list-repos@main
  with:
    github-token: ${{ github.token }}
    user: octocat
    fork: false
    archived: false
    filter-paths: |
      .copier-answers.ci.yml
```

Use the saved repository file in a later step:

```yaml
- name: List template-managed repositories
  id: managed
  uses: athackst/ci/actions/list-repos@main
  with:
    github-token: ${{ github.token }}
    user: octocat
    fork: false
    archived: false
    filter-paths: |
      .copier-answers.ci.yml

- name: Generate workflow status page
  run: python3 .github/scripts/generate_workflow_status.py --repos-file "${{ steps.managed.outputs.repository-file }}"
```

Local usage:

```bash
python3 actions/list-repos/list_repos.py \
  --user octocat \
  --fork false \
  --archived false \
  --filter-path .copier-answers.ci.yml
```

Profile a local run:

```bash
python3 actions/list-repos/list_repos.py \
  --user octocat \
  --fork false \
  --archived false \
  --filter-path .copier-answers.ci.yml \
  --debug-timing > /tmp/repositories.json
```

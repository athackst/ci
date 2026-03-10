# List Repos

List repositories for a GitHub user and return a filtered JSON array of repository full names.

## Usage

```yaml
- name: List repositories
  id: repos
  uses: athackst/ci/actions/list-repos@main
  with:
    github-token: ${{ github.token }}
    user: octocat
    private: false
    fork: false
    archived: false

- name: Show repositories
  shell: bash
  run: |
    echo '${{ steps.repos.outputs.repository }}'
```

## Inputs

| Name | Type | Description | Default |
| --- | --- | --- | --- |
| `github-token` | `string` | (optional) GitHub token used for GitHub API access. | `${{ github.token }}` |
| `user` | `string` | (optional) GitHub username whose repositories should be listed. | `${{ github.repository_owner }}` |
| `private` | `boolean` | (optional) Include only private repositories. | `false` |
| `fork` | `boolean` | (optional) Include only fork repositories. | `false` |
| `archived` | `boolean` | (optional) Include only archived repositories. | `false` |

## Outputs

| Name | Description |
| --- | --- |
| `repository` | JSON array of matching repository full names. |

## Permissions

- Requires a token that `gh` can use for GitHub API access.
- Private repository listing requires a token for the target user account.

## Advanced

- The action supports GitHub users only and fails for organizations.
- User repositories are queried from `/users/<user>/repos` for public access and `/user/repos` when `private: true`.
- Results are paginated in batches of 100.
- Filtering for `private`, `fork`, and `archived` is applied locally after each API response.
- The `repository` output is a JSON array string such as `["owner/repo-a","owner/repo-b"]`.

## Examples

List private repositories with an explicit token:

```yaml
- name: List private repositories
  id: private-repos
  uses: athackst/ci/actions/list-repos@main
  with:
    github-token: ${{ secrets.CI_BOT_TOKEN }}
    user: octocat
    private: true
```

Only archived repositories:

```yaml
- name: List archived repositories
  id: archived
  uses: athackst/ci/actions/list-repos@main
  with:
    github-token: ${{ github.token }}
    user: octocat
    archived: true
```

Only fork repositories:

```yaml
- name: List fork repositories
  id: forks
  uses: athackst/ci/actions/list-repos@main
  with:
    github-token: ${{ github.token }}
    user: octocat
    fork: true
```

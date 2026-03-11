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
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `github-token` | (optional) GitHub token used for GitHub API access. | `${{ github.token }}` |
| `user` | (optional) GitHub username whose repositories should be listed. | `${{ github.repository_owner }}` |
| `private` | (optional) Include only private repositories. | `false` |
| `fork` | (optional) Include only fork repositories. | `false` |
| `archived` | (optional) Include only archived repositories. | `false` |

## Outputs

| Name | Description |
| --- | --- |
| `repository` | JSON array of matching repository full names. |

## Permissions

- Public repository listing works with the default token.
- Listing private repositories requires a token that can read the target user's private repositories.

## Advanced

- Supports GitHub users only and fails for organizations.
- When `private: true`, repositories are queried from the authenticated `/user/repos` endpoint and then filtered to the requested owner.
- `private`, `fork`, and `archived` are exact-match filters, not inclusive toggles.
- The `repository` output is a JSON array string such as `["owner/repo-a","owner/repo-b"]`.

## Examples

List only archived repositories:

```yaml
- name: List archived repositories
  id: archived
  uses: athackst/ci/actions/list-repos@main
  with:
    github-token: ${{ github.token }}
    user: octocat
    archived: true
```


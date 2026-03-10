# Resolve Config

Resolve a config file from the local workspace or fetch it from the GitHub Contents API into a runner-local file.

## Usage

```yaml
- name: Resolve config
  id: config
  uses: athackst/ci/actions/resolve-config@main
  with:
    configuration-path: .github/ci-config.yml
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `configuration-path` | Path to the config file in the workspace or repository. | None |
| `output-path` | (optional) Runner-local file path for the resolved config contents. | `${{ runner.temp }}/resolved-config.yml` |
| `repo` | (optional) Repository in `owner/repo` format used for API fetch. | `${{ github.repository }}` |
| `ref` | (optional) Git ref or SHA used for API fetch. | `${{ github.sha }}` |
| `github-token` | (optional) GitHub token used for API fetch. | `${{ github.token }}` |

## Outputs

| Name | Description |
| --- | --- |
| `source-config-path` | Source location used to resolve the config. |
| `config-path` | Runner-local file path to the resolved config. |

## Permissions

- Local workspace resolution does not require special permissions.
- API fallback requires a token that can read repository contents. `contents: read` is typically sufficient.

## Advanced

- If `configuration-path` exists locally, that file is used directly.
- If it does not exist locally, the action fetches the file from the GitHub Contents API using `repo` and `ref`.
- `config-path` always points to a local file on the runner, even when the source came from the API.
- `source-config-path` reports either the local path or a `repo@ref:path` source string.

## Examples

Resolve config from another repository ref:

```yaml
- name: Resolve shared config
  id: config
  uses: athackst/ci/actions/resolve-config@main
  with:
    configuration-path: .github/ci-config.yml
    repo: athackst/ci
    ref: main
    github-token: ${{ secrets.CI_BOT_TOKEN }}
```


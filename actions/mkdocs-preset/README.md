# MkDocs Site Preset

Build or serve a MkDocs site with the managed CI preset, theme overrides, and containerized toolchain. Generated configuration is kept inside the action container; only the built site is written to the workspace.

## Usage

```yaml
- name: Build MkDocs site
  id: site
  uses: athackst/ci/actions/mkdocs-preset@main
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `docs-dir` | Documentation source directory, relative to the workspace. (optional) | `docs` |
| `site-dir` | Built site directory, relative to the workspace. (optional) | `site` |
| `site-name` | The name of the documentation site. (optional) | `${{ github.repository }}` |
| `repo-url` | The source repository URL. (optional) | `https://github.com/${{ github.repository }}` |
| `site-url` | The canonical URL of the generated site. (optional) | `""` |
| `edit-uri` | The repository-relative edit URI. (optional) | `edit/main/` |

## Outputs

| Name | Description |
| --- | --- |
| `site-path` | Relative path to the built site in the workspace. |

## Advanced

- Uses a Docker container so local preview and CI use the same MkDocs toolchain.
- Resolves `docs_dir`, `site_dir`, and theme overrides to explicit paths because the generated `mkdocs.yml` is kept outside the repository workspace.
- Runs `mkdocs build` when used as a GitHub Action.
- The container also accepts `serve` as its command for local live preview.
- The managed configuration is regenerated on every run and is not written into the repository.

## Examples

Build and upload the generated site:

```yaml
- name: Build MkDocs site
  id: site
  uses: athackst/ci/actions/mkdocs-preset@main
  with:
    site-url: https://example.github.io/project/

- name: Upload site
  uses: actions/upload-pages-artifact@v5
  with:
    path: ${{ steps.site.outputs.site-path }}
```

Run the published image locally:

```bash
docker run --rm -it \
  --user "$(id -u):$(id -g)" \
  -p 8000:8000 \
  -v "$PWD:/github/workspace" \
  ghcr.io/athackst/ci/mkdocs-preset:latest serve
```

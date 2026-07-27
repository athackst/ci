# Jekyll Site Preset

Build or serve a Jekyll site with the managed CI configuration, theme, semiliterate extraction, and containerized toolchain. Generated configuration and extracted source stay inside the action container; only the built site is written to the workspace.

## Usage

```yaml
- name: Build Jekyll site
  id: site
  uses: athackst/ci/actions/jekyll-preset@main
  env:
    JEKYLL_GITHUB_TOKEN: ${{ github.token }}
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `source` | Site source directory, relative to the workspace. (optional) | `.` |
| `site-dir` | Built site directory, relative to the workspace. (optional) | `_site` |
| `title` | The title of the site. (optional) | `${{ github.repository }}` |
| `description` | A short description of the site. (optional) | `""` |
| `image` | The social preview image URL. (optional) | `""` |
| `edit-url` | The URL used for edit links. (optional) | `https://www.github.com/${{ github.repository }}/edit/main/` |
| `nav-filename` | The navigation file name. (optional) | `.nav.yml` |
| `versions-config` | The location of the versions manifest. (optional) | `""` |
| `base-path` | The root site path used by the version selector. (optional) | `""` |
| `base-url` | The base URL path passed to Jekyll. (optional) | `""` |
| `semiliterate` | Extract source content with semiliterate before building. (optional) | `true` |

## Outputs

| Name | Description |
| --- | --- |
| `site-path` | Relative path to the built site in the workspace. |

## Permissions

When `github.token` is passed as `JEKYLL_GITHUB_TOKEN`, `contents: read` is sufficient.

## Advanced

- Uses the bundled Jekyll configuration and gems rather than repository-managed config files.
- Runs semiliterate extraction in temporary container storage when `semiliterate` is enabled.
- Runs `jekyll build` when used as a GitHub Action.
- The container accepts `serve` for local preview on port 4000.
- Local `serve` performs semiliterate extraction once at startup; restart the container to extract subsequent source changes.

## Examples

Run the published image locally:

```bash
docker run --rm -it \
  --user "$(id -u):$(id -g)" \
  -p 4000:4000 \
  -v "$PWD:/github/workspace" \
  ghcr.io/athackst/ci:jekyll-preset-latest serve
```

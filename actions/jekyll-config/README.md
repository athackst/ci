# Configure Jekyll for GitHub Pages

Render the bundled Jekyll configuration and copy its managed dependencies into a selected directory.

## Usage

```yaml
- name: Configure Jekyll
  id: jekyll-config
  uses: athackst/ci/actions/jekyll-config@main
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `title` | The title of the site. | `${{ github.repository }}` |
| `description` | The site description. (optional) | `""` |
| `image` | The social preview image URL. (optional) | `""` |
| `edit_url` | The URL used for edit links. (optional) | `https://www.github.com/${{ github.repository }}/edit/main/` |
| `nav_filename` | The navigation file name. (optional) | `.nav.yml` |
| `versions_config` | The versions config path written into `versions.config`. Use a root-relative Pages path such as `/ci/versions.json`. When empty, versioning stays disabled. (optional) | `""` |
| `base_path` | The site base path written into `versions.prefix`, for example `/ci`. (optional) | `""` |
| `output-directory` | Directory where the managed Jekyll files are written. (optional) | `.` |

## Outputs

| Name | Description |
| --- | --- |
| `gemfile-path` | Path to the generated `Gemfile`. |
| `config-path` | Path to the generated `_config.yml`. |
| `semiliterate-config-path` | Path to the generated `semiliterate.yml`. |

## Advanced

- Replaces the managed `_config.yml`, `Gemfile`, and `semiliterate.yml` on every run.
- Resolves dependencies from the managed `Gemfile` by clearing the destination `Gemfile.lock`.
- Keeps the generated files together under `output-directory`.
- Renders the bundled `_config.yml` template with the provided metadata and GitHub repository context.
- Sets `versions.enabled` automatically based on whether `versions_config` is empty.
- Writes the provided `versions_config` value directly to `versions.config`.
- Writes the provided `base_path` value directly to `versions.prefix`.
- Exposes the generated file locations as outputs so later steps can reuse the resolved paths directly.
- For GitHub Pages sites published under a subpath, prefer a root-relative path so versioned pages resolve the shared manifest correctly.

## Examples

Enable versioned docs with a root-relative Pages manifest:

```yaml
- name: Configure Jekyll
  id: jekyll-config
  uses: athackst/ci/actions/jekyll-config@main
  with:
    title: My Docs
    description: Project documentation
    versions_config: /ci/versions.json
    base_path: /ci
    output-directory: ${{ runner.temp }}/jekyll

- run: bundle exec jekyll build --config "${{ steps.jekyll-config.outputs.config-path }}"
  env:
    BUNDLE_GEMFILE: ${{ steps.jekyll-config.outputs.gemfile-path }}
```

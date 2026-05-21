# Configure Jekyll for GitHub Pages

Create the baseline Jekyll files used by this CI setup and render the bundled site config into the workspace.

## Usage

```yaml
- name: Configure Jekyll
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

## Advanced

- Creates `_config.yml`, `Gemfile`, and `semiliterate.yml` only when they do not already exist.
- Renders the bundled `_config.yml` template with the provided metadata and GitHub repository context.
- Sets `versions.enabled` automatically based on whether `versions_config` is empty.
- Writes the provided `versions_config` value directly to `versions.config`.
- Writes the provided `base_path` value directly to `versions.prefix`.
- For GitHub Pages sites published under a subpath, prefer a root-relative path so versioned pages resolve the shared manifest correctly.

## Examples

Enable versioned docs with a root-relative Pages manifest:

```yaml
- name: Configure Jekyll
  uses: athackst/ci/actions/jekyll-config@main
  with:
    title: My Docs
    description: Project documentation
    versions_config: /ci/versions.json
    base_path: /ci
```

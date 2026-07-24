# Jekyll Site

Build a Jekyll site and upload a Pages-compatible artifact for downstream testing or deployment.

## Usage

```yaml
jobs:
  site:
    uses: athackst/ci/.github/workflows/jekyll_site.yml@main
    with:
      version: dev
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `source` | (optional) Source directory for the site. | `.` |
| `version` | (optional) Version path to append to the site base path, for example `dev` or `1.2.3`. | `""` |
| `semiliterate` | (optional) Extract docs with semiliterate before building. | `true` |
| `artifact-name` | (optional) Artifact name for the built site. | `github-pages` |
| `host` | (optional) Site host or origin, such as `docs.example.com` or `https://docs.example.com`. | `""` |
| `base-path` | (optional) Path beneath `host`, such as `/project`. | `""` |
| `base-url` | (optional) Full site base URL. Derived from `host` and `base-path` when omitted. | `""` |

## Outputs

| Name | Description |
| --- | --- |
| `host` | Host name for the site. |
| `base-path` | Base path for the site. |
| `base-url` | Base URL for the site. |
| `version` | Version identifier passed to the build. |
| `artifact-name` | Name of the uploaded site artifact. |

## Permissions

- Build uses `contents: read` in the caller job.
- GitHub Pages location resolution uses `pages: read`.

## Advanced

- Uses `configure-site` to resolve a GitHub Pages location or an explicit hosting location.
- An empty `host` selects GitHub Pages metadata; explicit `base-path` and `base-url` values accompany an explicit `host`.
- Uses the bundled `jekyll-config` action before building the site.
- Optionally extracts source content with `PrimerPages/semiliterate`.
- The workflow outputs retain the root site location; `version` is appended to the base path passed to Jekyll.
- Versioned builds enable the shared versions manifest used by the theme's version selector.
- Exposes site metadata outputs for downstream workflows such as HTMLProofer and site deploy.
- This workflow only builds and uploads the site artifact. HTMLProofer and deployment are handled by separate reusable workflows.

## Examples

Build site:

```yaml
jobs:
  site:
    uses: athackst/ci/.github/workflows/jekyll_site.yml@main
```

Build versioned docs:

```yaml
jobs:
  site:
    uses: athackst/ci/.github/workflows/jekyll_site.yml@main
    with:
      version: dev
```

Build for an externally hosted site:

```yaml
jobs:
  site:
    uses: athackst/ci/.github/workflows/jekyll_site.yml@main
    with:
      host: docs.example.com
      base-path: /project
```

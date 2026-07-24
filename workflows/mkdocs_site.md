# MkDocs Site

Build a MkDocs site and upload a Pages-compatible artifact for downstream testing or deployment.

## Usage

```yaml
jobs:
  site:
    uses: athackst/ci/.github/workflows/mkdocs_site.yml@main
    with:
      version: dev
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `artifact-name` | (optional) Artifact name for the built site. | `github-pages` |
| `version` | (optional) Version path to append to the site base path, for example `dev` or `1.2.3`. | `""` |

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

- Uses GitHub Pages metadata for the root site location.
- Uses the bundled `mkdocs-config` action before building the site.
- Exposes site metadata outputs for downstream workflows such as HTMLProofer and site deploy.
- The workflow outputs retain the root site location; `version` is appended to the URL passed to MkDocs.
- This workflow only builds and uploads the site artifact. HTMLProofer and deployment are handled by separate reusable workflows.

## Examples

Build site:

```yaml
jobs:
  site:
    uses: athackst/ci/.github/workflows/mkdocs_site.yml@main
```

Build versioned docs:

```yaml
jobs:
  site:
    uses: athackst/ci/.github/workflows/mkdocs_site.yml@main
    with:
      version: dev
```

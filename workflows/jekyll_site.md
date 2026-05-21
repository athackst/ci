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
| `version` | (optional) Version path to append to the site base path, for example `dev` or `1.2.3`. | `""` |
| `semiliterate` | (optional) Extract docs with semiliterate before building. | `true` |
| `artifact-name` | (optional) Artifact name for the built site. | `github-pages` |

## Permissions

- Build only needs `contents: read` in the caller job.

## Advanced

- Uses the bundled `jekyll-config` action before building the site.
- Optionally extracts source content with `PrimerPages/semiliterate`.
- Exposes `host`, `base-path`, `version`, and `artifact-name` outputs for downstream workflows such as HTMLProofer and site deploy.
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

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

## Permissions

- Build only needs `contents: read` in the caller job.

## Advanced

- Uses the bundled `mkdocs-config` action before building the site.
- Exposes `host`, `base-path`, `version`, and `artifact-name` outputs for downstream workflows such as HTMLProofer and site deploy.
- When `version` is non-empty, the build output is prepared under a versioned base path such as `/repo/dev` or `/repo/1.2.3`.
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

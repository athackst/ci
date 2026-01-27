# buildsmith

Central home for my reusable GitHub Actions workflows and composite actions.

This repo is meant to be referenced directly from other repos via `workflow_call`
or by using the composite actions under `actions/`.

## Reusable workflows

Workflows live in `workflows/` and are called from another repo like this:

```yaml
jobs:
  pr-labels:
    uses: athackst/buildsmith/workflows/pr_labeler.yml@main
    secrets: inherit
```

```yaml
jobs:
  release:
    uses: athackst/buildsmith/workflows/release_draft.yml@main
    with:
      bump_script: .github/bump.sh
      github_token: ${{ secrets.RELEASE_TOKEN }}
```

```yaml
jobs:
  docs:
    uses: athackst/buildsmith/workflows/jekyll.yml@main
```

```yaml
jobs:
  docs:
    uses: athackst/buildsmith/workflows/mkdocs.yml@main
```

Available workflows:

- `pr_labeler.yml` - Apply labels to PRs based on branch naming.
- `release_draft.yml` - Draft release notes and optionally run a bump script.
- `jekyll.yml` - Build, test, and deploy a Jekyll site to GitHub Pages.
- `mkdocs.yml` - Build, test, and deploy MkDocs to GitHub Pages.

## Composite actions

Composite actions live in `actions/` and can be used directly:

### PR labeler

```yaml
steps:
  - uses: athackst/buildsmith/actions/pr-labeler@main
    with:
      github_token: ${{ secrets.GITHUB_TOKEN }}
```

### Release draft

```yaml
steps:
  - uses: athackst/buildsmith/actions/release-draft@main
    id: draft
    with:
      github_token: ${{ secrets.GITHUB_TOKEN }}
  - run: echo "Drafted tag: ${{ steps.draft.outputs.tag_name }}"
```


This is just a test change

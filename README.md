# ci

Central home for my reusable GitHub Actions workflows and composite actions.

This repo is meant to be referenced directly from other repos via `workflow_call`
or by using the composite actions under `actions/`.

## Reusable workflows

Reusable workflows live in `.github/workflows/` and are called from another repo like this:

```yaml
jobs:
  pr-labels:
    uses: athackst/ci/.github/workflows/pr_labeler.yml@main
    secrets: inherit
```

```yaml
jobs:
  draft-release:
    uses: athackst/ci/.github/workflows/release_drafter.yml@main
    secrets:
      token: ${{ secrets.RELEASE_TOKEN }}
```

```yaml
jobs:
  docs:
    uses: athackst/ci/.github/workflows/mkdocs_site.yml@main
```

```yaml
jobs:
  jekyll-docs:
    uses: athackst/ci/.github/workflows/jekyll_site.yml@main
    with:
      path: docs
```

```yaml
jobs:
  pr-bump:
    uses: athackst/ci/.github/workflows/pr_bump.yml@main
    with:
      bump-script: scripts/bump_version.sh
    secrets:
      token: ${{ secrets.BOT_TOKEN }}
```

```yaml
jobs:
  pr-automerge:
    uses: athackst/ci/.github/workflows/automerge.yml@main
    secrets:
      token: ${{ secrets.BOT_TOKEN }}
```

```yaml
jobs:
  ci-update:
    uses: athackst/ci/.github/workflows/ci_updater.yml@main
    with:
      create-pr: true
    secrets:
      token: ${{ secrets.BOT_TOKEN }}
```

Available workflows:

- `pr_labeler.yml` - Apply labels to PRs based on branch naming.
- `pr_bump.yml` - Resolve version metadata and run an optional bump script, committing changes to a target branch when a bump is needed.
- `automerge.yml` - Enable GitHub auto-merge for labeled PRs.
- `ci_updater.yml` - Run Copier updates and open/update a PR with template changes (outputs are derived from `create-pull-request` results).
- `release_drafter.yml` - Resolve version metadata, generate changelog, and create/update a draft release.
- `mkdocs_site.yml` - Build, test, and deploy MkDocs to GitHub Pages.
- `jekyll_site.yml` - Build, test, and deploy Jekyll to GitHub Pages.

## Composite actions

Composite actions live in `actions/` and can be used directly:

### PR labeler

```yaml
steps:
  - uses: athackst/ci/actions/pr-labeler@main
    with:
      github_token: ${{ secrets.GITHUB_TOKEN }}
```

### Version resolver

```yaml
steps:
  - uses: athackst/ci/actions/version-resolver@main
    id: version
    with:
      gh-token: ${{ secrets.GITHUB_TOKEN }}
  - run: echo "Resolved version: ${{ steps.version.outputs.resolved-version }}"
```

### Changelog

```yaml
steps:
  - uses: athackst/ci/actions/changelog@main
    id: changelog
    with:
      pr-info-path: ${{ steps.version.outputs.pr-info-path }}
  - run: echo "${{ steps.changelog.outputs.changelog }}"
```

### Release draft

```yaml
steps:
  - uses: athackst/ci/actions/release-draft@main
    id: draft
    with:
      token: ${{ secrets.GITHUB_TOKEN }}
      name: Release v1.2.3
      tag-name: v1.2.3
      changelog: ${{ steps.changelog.outputs.changelog }}
  - run: echo "Draft release id: ${{ steps.draft.outputs.id }}"
```

## Copier template

This repo includes a Copier template in `template/` so other repos can sync
workflow defaults from this repository.

Install Copier (pick one):

```bash
# recommended
pipx install copier

# or
python3 -m pip install --user copier

# one-shot (no install)
uvx copier --help
```

Use it from another repository:

```bash
# Initial apply from this repo
copier copy --trust gh:athackst/ci .

# Update later
copier update --trust
```

Template files:

- `template/.github/workflows/pr_bot.yml.jinja`
- `template/.github/workflows/release_draft.yml.jinja`
- `template/.github/workflows/site.yml.jinja` (`mkdocs` or `jekyll`)
- `template/.github/workflows/ci_update.yml.jinja` (daily scheduled CI template updates)

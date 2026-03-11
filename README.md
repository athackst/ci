# ci

Central home for my reusable GitHub Actions workflows and composite actions.

The main assumption of this repo is that consumer repositories adopt it via the
Copier template first. After that, the primary entrypoints in the consumer repo
should be the generated workflows:

- `ci_update.yml`
- `pr_bot.yml`
- `release_draft.yml`
- `site.yml`

Those workflows keep the consumer repo aligned with this central CI repo,
handle common PR automation, create release drafts, and set up site builds.

## Usage

Install Copier (pick one):

```bash
# recommended
pipx install copier

# or
python3 -m pip install --user copier

# one-shot (no install)
uvx copier --help
```

Bootstrap a repository with my defaults:

```bash
copier copy --trust gh:athackst/ci .
```

Or use the helper script in this repo to apply the template and set the secret:

```bash
tools/init_ci_repo.sh --repo owner/repo
```

Add the `CI_BOT_TOKEN` token to the repository with the following permissions:

- `contents: write`
- `pull requests: write`
- `issues: write`
- `actions: write`

Why:

- `ci_update.yml` needs to push template-sync branches and open or update PRs.
- `pr_bot.yml` uses the token for automerge and optional `pr_bump.yml` pushes.
- `ci_updater.yml` may need `actions: write` when template updates modify `.github/workflows/*`.

## Mental model

This repo is opinionated around one shared CI config file, `.github/ci-config.yml`,
which drives:

- PR labels
- release notes categories
- semantic version resolution
- repository label metadata

The workflows are meant to compose around that config instead of each repository
re-declaring the same rules in multiple places.

## Configuration

Copier asks a small number of questions and uses the answers to generate the
entrypoint workflows plus a shared CI config.

### Copier questions

`bump_script_path`

- Optional path to a script in the target repository.
- If set, `pr_bot.yml` will also run `pr_bump.yml` for trusted same-repo PRs.
- Leave it empty if the repo does not maintain a version file, changelog file, or other bumpable artifact in PRs.

`site_generator`

- Chooses whether `site.yml` uses MkDocs or Jekyll.
- `mkdocs` is the default and matches the rest of this repo most closely.
- `jekyll` is there for repositories that already have an established Jekyll site.

`site_version`

- Only shown for MkDocs sites.
- When enabled, `site.yml` publishes versioned docs:
  `main` publishes `dev`, and release events publish the release tag plus `latest`.
- Leave it off for a simpler single-version docs site.

`release_template`

- Contents for `.github/release_template.md`.
- Used by `release_draft.yml` when rendering the draft release body.
- Supports `$CHANGES` for generated changelog content and `$VERSION` / `$RESOLVED_VERSION` for the resolved version.

### Generated files

The template writes these main files into the target repository:

- `.github/workflows/ci_update.yml`
- `.github/workflows/pr_bot.yml`
- `.github/workflows/release_draft.yml`
- `.github/workflows/site.yml`
- `.github/ci-config.yml`
- `.github/release_template.md`

### Shared CI config

`.github/ci-config.yml` is the center of the convention. It combines concepts
that would normally live in separate files:

- release-drafter categories and templates
- version-resolver label rules
- PR labeler rules
- repository label metadata such as label descriptions and colors

This is intentionally a modified combination of the upstream
[release-drafter/release-drafter](https://github.com/release-drafter/release-drafter)
and [actions/labeler](https://github.com/actions/labeler) config formats.

**Modifications to `release-drafter.yml`**

- Adds `template-file` so the release body can live in `.github/release_template.md` instead of being embedded in YAML.

**Modifications to `labeler.yml`**

- Adds `color` and `description` metadata to labels so the same config can also drive repository label setup.

Colors are set according to the following label palette:

| Label | Color | Preview |
| --- | --- | --- |
| `major` | `#b91c1c` | ![major](https://img.shields.io/badge/major-b91c1c?style=flat-square) |
| `fix` | `#ea580c` | ![fix](https://img.shields.io/badge/fix-ea580c?style=flat-square) |
| `feature` | `#0f766e` | ![feature](https://img.shields.io/badge/feature-0f766e?style=flat-square) |
| `documentation` | `#65a30d` | ![documentation](https://img.shields.io/badge/documentation-65a30d?style=flat-square) |
| `maintenance` | `#7c3aed` | ![maintenance](https://img.shields.io/badge/maintenance-7c3aed?style=flat-square) |
| `dependencies` | `#2563eb` | ![dependencies](https://img.shields.io/badge/dependencies-2563eb?style=flat-square) |
| `devops` | `#0ea5e9` | ![devops](https://img.shields.io/badge/devops-0ea5e9?style=flat-square) |
| `automerge` | `#eab308` | ![automerge](https://img.shields.io/badge/automerge-eab308?style=flat-square) |

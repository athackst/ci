# ci

Central home for my reusable GitHub Actions workflows and composite actions.

The main assumption of this repo is that consumer repositories adopt it via the
Copier template first. After that, the primary entrypoints in the consumer repo
should be the generated workflows:

- `ci_update.yml`
- `pr_bot.yml`
- `release_draft.yml`
- `site.yml` when a site workflow is enabled

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

- Chooses whether to generate `site.yml`, and if so whether it uses MkDocs or Jekyll.
- `none` is the default and skips site workflow generation entirely.
- `mkdocs` matches the rest of this repo most closely.
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
- `.github/workflows/site.yml` when `site_generator` is not `none`
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
| `breaking` | `#7f1d1d` | ![breaking](https://img.shields.io/badge/breaking-7f1d1d?style=flat-square) |
| `bug` | `#d73a4a` | ![bug](https://img.shields.io/badge/bug-d73a4a?style=flat-square) |
| `enhancement` | `#0f766e` | ![enhancement](https://img.shields.io/badge/enhancement-0f766e?style=flat-square) |
| `maintenance` | `#0ea5e9` | ![maintenance](https://img.shields.io/badge/maintenance-0ea5e9?style=flat-square) |
| `dependencies` | `#1d4ed8` | ![dependencies](https://img.shields.io/badge/dependencies-1d4ed8?style=flat-square) |
| `documentation` | `#64748b` | ![documentation](https://img.shields.io/badge/documentation-64748b?style=flat-square) |
| `automerge` | `#ca8a04` | ![automerge](https://img.shields.io/badge/automerge-ca8a04?style=flat-square) |
| `good first issue` | `#c4b5fd` | ![good first issue](https://img.shields.io/badge/good%20first%20issue-c4b5fd?style=flat-square) |
| `help wanted` | `#db2777` | ![help wanted](https://img.shields.io/badge/help%20wanted-db2777?style=flat-square) |
| `question` | `#7e22ce` | ![question](https://img.shields.io/badge/question-7e22ce?style=flat-square) |
| `duplicate` | `#cbd5e1` | ![duplicate](https://img.shields.io/badge/duplicate-cbd5e1?style=flat-square) |
| `invalid` | `#a3a3a3` | ![invalid](https://img.shields.io/badge/invalid-a3a3a3?style=flat-square) |
| `wontfix` | `#78716c` | ![wontfix](https://img.shields.io/badge/wontfix-78716c?style=flat-square) |

### Setting up GitHub App for `ci_update_dispatch.yml`

The central dispatcher workflow in this repository, [`ci_update_dispatch.yml`](https://github.com/athackst/ci/blob/main/.github/workflows/ci_update_dispatch.yml), also requires a GitHub App so it can discover managed repositories, read their `.copier-answers.ci.yml` files, refresh the public workflow status page, and send `repository_dispatch` events.

Setup notes:

1. Create a GitHub App owned by the same account or organization that owns this repo.
2. Install the app on this repo and on every repository that should receive `ci-update` dispatches.
3. In this repo, add these Actions secrets:
   - `APP_ID`: the GitHub App ID
   - `APP_PRIVATE_KEY`: the GitHub App private key PEM
4. In the app repository permissions, grant `Contents: Read and write`.
   This is needed because:
   - the dispatcher needs to read `.copier-answers.ci.yml` from installed repositories
   - `repository_dispatch` is sent through the repository contents API surface and requires write-level access
   - write access also covers the read access needed for repo matching
5. If the dispatcher stops matching or dispatching repos, first confirm the app is still installed on the target repositories and that the private key in `APP_PRIVATE_KEY` is current.

# ci

Central home for my reusable GitHub Actions workflows and composite actions.

The main assumption of this repo is that consumer repositories adopt it through
the Copier template first. After that, the primary entrypoints in the consumer
repo are the generated workflows:

- `ci_update.yml`
- `pr_automerge.yml`
- `pr_labeler.yml`
- `setup_labels.yml`
- `pr_bump.yml` when `bump_script_path` is set
- `release_draft.yml` when `do_releases` is enabled
- `site.yml` when a site workflow is enabled

Those workflows keep the consumer repo aligned with this central CI repo,
handle common PR automation, create release drafts, sync repository labels, and
set up site builds.

## Usage

### Quick start

```bash
tools/init_ci_repo.sh
```

The helper applies the Copier template, then asks whether to set
`CI_BOT_TOKEN` with `gh secret set`. It can infer the repository from a GitHub
git remote or `gh repo view`; otherwise pass `--repo owner/repo`. Pass extra
Copier options after `--`.

### Manual setup

Install Copier:

```bash
pipx install copier
```

Apply the template:

```bash
copier copy --trust gh:athackst/ci .
```

Add a repository secret named `CI_BOT_TOKEN`:

1. Create a Fine-grained personal access token for the target repository.
2. In the repository, go to `Settings -> Secrets and variables -> Actions`.
3. Add a new repository secret named `CI_BOT_TOKEN` with that token value.

Required repository permissions for the token:

- `Contents: Read and write` for update and bump commits.
- `Pull requests: Read and write` for PR labels, comments, updater PRs, bump PRs, and automerge.
- `Issues: Read and write` for repository labels, PR comments, and failure issues.
- `Actions: Read and write` for updater PRs that modify workflow files.
- `Workflows: Read and write` for commits that create or update workflow files.
- `Variables: Read and write` for generated `release_draft.yml` workflows that persist `DRAFT_RELEASE_ID`.

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

- Optional shell command to run in the target repository after version metadata is resolved.
- If set, the template generates `pr_bump.yml`.
- The command receives `VERSION`, `MAJOR_VERSION`, `MINOR_VERSION`, and `PATCH_VERSION`.
- Leave it empty if the repo does not maintain a version file, changelog file, or other bumpable artifact in PRs.

`site_generator`

- Chooses whether to generate `site.yml`, and if so whether it uses MkDocs or Jekyll.
- `none` is the default and skips site workflow generation entirely.
- `mkdocs` uses `mkdocs_site.yml`.
- `jekyll` uses `jekyll_site.yml`.
- MkDocs site workflows run on `main` pushes and release publishes; Jekyll site workflows run on `main` pushes.

`automerge_mode`

- Chooses how `pr_automerge.yml` handles labeled pull requests.
- `poll` is the default and waits for checks before merging directly, which works on private repos without GitHub native auto-merge support.
- `native` enables GitHub auto-merge for labeled PRs and lets GitHub merge when requirements are met.
- `disabled` keeps the workflow in place but disables automerge actions.

`do_releases`

- Chooses whether to generate `release_draft.yml`.
- When enabled, `release_draft.yml` creates or updates a draft release on `main` pushes.
- With MkDocs sites, this also publishes versioned docs:
  `main` publishes `dev`, and release events publish the release tag plus `latest`.
- When disabled, release draft generation is skipped and MkDocs sites publish a simpler unversioned Pages site.

`release_template`

- Contents for `.github/release_template.md`.
- Used by `release_draft.yml` when rendering the draft release body.
- Supports `$CHANGES` for generated changelog content and `$VERSION` / `$RESOLVED_VERSION` for the resolved version.
- Only asked when `do_releases` is enabled.

### Shared CI config

`.github/ci-config.yml` is the center of the convention. It combines concepts
that would normally live in separate files:

- release-drafter categories and templates
- version-resolver label rules
- PR labeler rules
- repository label metadata such as label descriptions and colors
- the release body template path

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
| `automerge` | `#eab308` | ![automerge](https://img.shields.io/badge/automerge-eab308?style=flat-square) |
| `good first issue` | `#c4b5fd` | ![good first issue](https://img.shields.io/badge/good%20first%20issue-c4b5fd?style=flat-square) |
| `help wanted` | `#db2777` | ![help wanted](https://img.shields.io/badge/help%20wanted-db2777?style=flat-square) |
| `question` | `#7e22ce` | ![question](https://img.shields.io/badge/question-7e22ce?style=flat-square) |
| `duplicate` | `#cbd5e1` | ![duplicate](https://img.shields.io/badge/duplicate-cbd5e1?style=flat-square) |
| `invalid` | `#a3a3a3` | ![invalid](https://img.shields.io/badge/invalid-a3a3a3?style=flat-square) |
| `wontfix` | `#78716c` | ![wontfix](https://img.shields.io/badge/wontfix-78716c?style=flat-square) |

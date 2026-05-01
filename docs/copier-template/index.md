# Copier Template

The Copier template generates the consumer-facing workflow files that call the
reusable workflows and actions from this repository.

Generated repositories always get:

- [`ci_update.yml`](./ci_update.md)
- [`pr_automerge.yml`](./pr_automerge.md)
- [`pr_labeler.yml`](./pr_labeler.md)
- [`setup_labels.yml`](./setup_labels.md)

Some workflows are conditional:

- [`pr_bump.yml`](./pr_bump.md) is generated when `bump_script_path` is set.
- [`release_draft.yml`](./release_draft.md) is generated when `do_releases` is enabled.
- [`site.yml`](./site.md) is generated when `site_generator` is `mkdocs` or `jekyll`.

The template also writes `.copier-answers.ci.yml`. It writes
`.github/ci-config.yml` and, when releases are enabled,
`.github/release_template.md` only when those files do not already exist.

## Token

Generated workflows use `CI_BOT_TOKEN` when an operation needs to write commits,
labels, PR comments, releases, workflow files, or repository variables. The
helper script `tools/init_ci_repo.sh` can set this secret with `gh secret set`.

Required repository permissions for the token:

- `Contents: Read and write`
- `Pull requests: Read and write`
- `Issues: Read and write`
- `Actions: Read and write`
- `Workflows: Read and write`
- `Variables: Read and write`

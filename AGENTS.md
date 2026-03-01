# CI Repo Engineering Contract

## Purpose

This repo is the source of truth for:

- Reusable workflows under `.github/workflows/*.yml`
- Composite actions under `actions/*`
- Copier templates under `template/`

Consumer repos should call workflows from this repo at `@main` unless explicitly pinning.

## Naming Conventions

- `action.yml` inputs/outputs: `kebab-case`
- CLI flags: `kebab-case`
- Python files/code: `snake_case`
- Shell env vars: `UPPER_SNAKE_CASE`
- JSON keys: `snake_case`

## Workflow Naming Policy

- Workflow display names (`name:`) should use `Title Case`.
- Workflow file names should use `snake_case.yml`.
- Test workflows should start with `Test ` in display names.
- Acronyms should use stable capitalization (`CI`, `PR`, `MkDocs`).

## Workflow Design Rules

- Reusable workflows should be opinionated; minimize optional knobs.
- Prefer one final `Workflow summary` step (`if: always()`) in workflows triggered by workflow_call.
- Prefer a test result step for every testing/validation job.
- Composite actions should emit outputs; workflow owns summary rendering.
- `GITHUB_OUTPUT`: prefer `| tee -a "$GITHUB_OUTPUT"` for log visibility.
- `GITHUB_STEP_SUMMARY`: prefer `>> "$GITHUB_STEP_SUMMARY"`.

## Reusable Workflow Source Policy

- Reusable workflows in this repo may intentionally reference `athackst/ci/...@main` when the goal is to validate published/default behavior.
- Branch-local behavior changes must be validated by local action/workflow tests (for example `./actions/...` in `test_actions.yml`).
- Template-generated consumer workflows should reference `athackst/ci/...@main` unless explicitly testing a pinned ref strategy.

## PR Event Model

- `pull_request_target` should be used for secret-requiring metadata operations.
- `pull_request` should be used for trusted same-repo mutation operations.
- Duplicate label/automerge runs are acceptable.
- `pr_bump` must not run on untrusted fork code paths.
- Dependabot/fork PRs may not have repository secrets on `pull_request`; route secret-requiring behavior through compatible event paths.

## Token Strategy

- Reusable workflows accept `secrets.token` as the canonical override.
- Templates map consumer secret `CI_BOT_TOKEN` -> `secrets.token`.
- `github.token` is fallback only.
- Dependabot/fork contexts may not have repo secrets on `pull_request`.

## Automerge Policy

- Label-driven: PRs with `automerge` label are auto-merged.

## Commenting Policy

- `pr_bump`: maintain a single updatable PR comment.
- `copier_update`: append-style comments are acceptable per commit-producing run.
- Do not comment on no-op runs.

## Copier Policy

- Template source is `template/` via `copier.yml` `_subdirectory`.
- `_answers_file` is `.copier-answers.ci.yml`.
- `ci_updater` uses `copier update` and requires answers file.
- `copier_update` (PR helper) uses `copier copy --defaults --overwrite`.
- `copier_update` should trigger only on template inputs (`copier.yml`, `template/**`) to avoid self-retrigger noise.

## Dispatch Policy

- Event type: `ci-update`.
- Dispatcher workflow sends `repository_dispatch` to target repos.
- Changed-path summaries in dispatcher should show only template files.

## Testing Policy

- `test_actions.yml`: action-level unit/integration checks.
- `test_workflows.yml`: reusable workflow behavior checks.
- `test_templates.yml`: Copier template rendering/lint checks.
- Prefer Bats for integration assertions; Python `unittest` for script logic.

## Security / Safety

- Never run untrusted PR code in `pull_request_target` mutation jobs.
- Keep permissions minimal per job.
- If broader permissions (for example `actions: write`) are used, add an in-file comment explaining why.
- Avoid destructive git operations; never hard reset in automation.

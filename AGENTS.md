# CI Repo Engineering Contract

## Purpose

This repo is the source of truth for:

- Reusable workflows under `.github/workflows/*.yml`
- Composite actions under `actions/*`
- Copier templates under `copier/template/`

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
- Test workflows should start with `Test` in display names.
- Acronyms should use stable capitalization (`CI`, `PR`, `MkDocs`).

## Workflow Design Rules

- Reusable workflows should be opinionated; minimize optional knobs.
- Prefer one final `Workflow summary` step (`if: always()`) in workflows triggered by workflow_call.
- Prefer a test result step for every testing/validation job.
- Composite actions should emit outputs; workflow owns summary rendering.
- Prefer script output as JSON and set `GITHUB_OUTPUT` keys explicitly in `action.yml` (instead of script-managed line output), for clearer output wiring and reviewability.
- Prefer Python logic in dedicated `.py` files under the action directory; avoid inline/heredoc Python in `action.yml` shell steps except for trivial one-liners.
- `GITHUB_OUTPUT`: prefer `| tee -a "$GITHUB_OUTPUT"` for log visibility.
- `GITHUB_STEP_SUMMARY`: prefer `>> "$GITHUB_STEP_SUMMARY"`.

## Reusable Workflow Source Policy

- Reusable workflows in this repo may intentionally reference `athackst/ci/...@main` when the goal is to validate published/default behavior.
- Branch-local behavior changes must be validated by local action/workflow tests (for example `./actions/...` in `test_actions.yml`).
- Template-generated consumer workflows should reference `athackst/ci/...@main` unless explicitly testing a pinned ref strategy.

## PR Event Model

- `pull_request_target` should be used for secret-requiring metadata operations.
- `pull_request` should be used for trusted same-repo mutation operations.
- Dependabot/fork PRs may not have repository secrets on `pull_request`; route secret-requiring behavior through compatible event paths.

## Token Strategy

- Reusable workflows accept `secrets.token` as the canonical override.
- Templates map consumer secret `CI_BOT_TOKEN` -> `secrets.token`.
- `github.token` is fallback only.
- Dependabot/fork contexts may not have repo secrets on `pull_request`.

## Automerge Policy

- Label-driven: PRs with `automerge` label are auto-merged.
- For label-driven automerge workflows that wait on checks, prefer per-PR concurrency with `cancel-in-progress: false`.
- Duplicate runs are acceptable if they preserve eventual merge behavior.

## Commenting Policy

- Do not comment on no-op runs.

## Copier Policy

- Template source is `copier/template/` via `copier.yml` `_subdirectory`.
- `_answers_file` is `.copier-answers.ci.yml`.
- `copier_update` and `ci_updater` use the `copier-update` action and require an answers file.
- The `copier-copy` action uses `copier copy --defaults --overwrite`.
- `test_templates` uses the `copier-copy` action to verify committed template outputs without mutating the repository.

## Dispatch Policy

- Event type: `ci-update`.
- Dispatcher workflow sends `repository_dispatch` to target repos.
- Changed-path summaries in dispatcher should show only template files.

## Testing Policy

- `test_actions.yml`: action-level unit/integration checks.
- `test_workflows.yml`: reusable workflow behavior checks.
- `test_templates.yml`: Copier template rendering, lint, and freshness checks.
- Action-specific tests belong under `actions/<action>/tests/`.
- Copier template-specific tests belong under `copier/tests/`.
- Repository-level and cross-cutting Bats tests belong under `tests/bats/`.
- Prefer Bats for integration assertions; Python `unittest` for script logic.

## Action README Format

- Action READMEs should use this section order:
- `# <Action Name>`
- Short description of the action
- `## Usage`
- `## Inputs` when inputs are specified
- `## Outputs` when outputs are specified
- `## Permissions` when token scopes matter
- `## Advanced` for non-obvious behavior or constraints users must know
- `## Examples`
- `Inputs` must use a table with columns: `Name`, `Description`, `Default`.  `Description` should include (optional) if it is optional.  Omit `Inputs` if no inputs are specified.
- Omit deprecated compatibility inputs from user-facing documentation.
- `Outputs` must use a table with columns: `Name`, `Description`. Omit `Outputs` if no outputs are specified.
- Keep `Usage` to the minimal working example first.
- Omit `Permissions` when no token scope guidance is needed.
- Omit `Examples` when `Usage` already covers the practical case.
- Keep `Advanced` concise and limited to non-obvious behavior that affects correct usage.
- `Advanced` should describe user-facing behavior and constraints, not internal implementation details.

## Reusable workflow documentation format

Reusable workflow documentation files are located in `workflows/`.

- Reusable workflow READMEs should use this section order:
- `# <Workflow Name>`
- Short description of the workflow
- `## Usage`
- `## Inputs` when inputs are specified
- `## Secrets` when secrets are specified
- `## Outputs` when outputs are specified
- `## Permissions` when callers need token scope guidance
- `## Advanced` for non-obvious behavior or constraints users must know
- `## Examples`
- `Inputs` must use a table with columns: `Name`, `Description`, `Default`. `Description` should include (optional) if it is optional. Omit `Inputs` if no inputs are specified.
- Omit deprecated compatibility inputs from user-facing documentation.
- `Secrets` must use a table with columns: `Name`, `Description`. `Description` should include (optional) if it is optional and describe fallback behavior when applicable. Omit `Secrets` if no secrets are specified.
- `Outputs` must use a table with columns: `Name`, `Description`. Omit `Outputs` if no outputs are specified.
- Keep `Usage` to the minimal working reusable workflow call first.
- `Usage` examples should show `uses: athackst/ci/.github/workflows/<file>.yml@main`.
- Omit `Permissions` when no caller guidance is needed.
- Omit `Examples` when `Usage` already covers the practical case.
- Keep `Advanced` concise and limited to non-obvious behavior that affects correct usage.
- `Advanced` should describe user-facing behavior and constraints, not internal implementation details.

## Security / Safety

- Never run untrusted PR code in `pull_request_target` mutation jobs.
- Keep permissions minimal per job.
- If broader permissions (for example `actions: write`) are used, add an in-file comment explaining why.
- When permissions change in reusable workflows under `.github/workflows/`, double-check corresponding files under `copier/template/.github/workflows/` to ensure caller-facing permissions still match the intended contract.
- Avoid destructive git operations; never hard reset in automation.

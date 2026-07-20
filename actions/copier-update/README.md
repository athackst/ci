# Copier Update

Install Copier and update a project from its answers file.

## Usage

```yaml
- name: Apply Copier update
  id: copier
  uses: athackst/ci/actions/copier-update@main
  with:
    answers-file: .copier-answers.ci.yml
    vcs-ref: HEAD
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `answers-file` | (optional) Copier answers file to use for the update. | `.copier-answers.yml` |
| `vcs-ref` | (optional) Copier template ref to update from. Copier selects the template version when omitted. | `""` |

## Outputs

| Name | Description |
| --- | --- |
| `answers-found` | Whether the configured answers file exists. |
| `command` | Shell-safe Copier command used for the update. |
| `changed` | Whether Copier produced file changes. |
| `changed-files` | Newline-delimited list of files changed by Copier. |
| `conflicts-found` | Whether Copier produced merge conflicts. |
| `conflicted-files` | Newline-delimited list of files with merge conflicts. |

## Advanced

- The configured answers file must exist.
- The action runs `copier update` with trusted template tasks, recorded answers, and default responses.
- Merge conflicts produce a failed action result and remain available through the conflict outputs.
- `command` is available for workflow summaries and manual recovery instructions.

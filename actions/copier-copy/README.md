# Copier Copy

Install Copier and render a template into a destination.

## Usage

```yaml
- name: Render Copier template
  id: copier
  uses: athackst/ci/actions/copier-copy@main
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `source` | (optional) Copier template source. | `.` |
| `destination` | (optional) Destination directory for rendered files. | `.` |
| `answers-file` | (optional) Answers file path relative to the destination. | `""` |
| `vcs-ref` | (optional) Copier template ref to copy from. Copier selects the template version when omitted. | `""` |
| `overwrite` | (optional) Whether to overwrite existing destination files. | `true` |

## Outputs

| Name | Description |
| --- | --- |
| `command` | Shell-safe Copier command used for the copy. |
| `changed` | Whether Copier produced file changes. |
| `changed-files` | Newline-delimited list of files changed by Copier. |

## Advanced

- The action runs `copier copy` with trusted template tasks, default responses, and optional overwriting.
- `answers-file` is resolved relative to `destination`.
- The action requires a clean checked-out Git worktree and reports changes across that worktree.
- `overwrite: false` protects existing files by failing when Copier requires an interactive collision decision.
- `command` is available for workflow summaries and manual recovery instructions.

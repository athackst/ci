# Configure MkDocs for GitHub Pages

Copy the bundled MkDocs configuration, dependencies, and theme overrides into a managed directory.

## Usage

```yaml
- name: Configure MkDocs
  id: mkdocs-config
  uses: athackst/ci/actions/mkdocs-config@main
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `output-directory` | Directory where the managed MkDocs files are written. (optional) | `.` |

## Outputs

| Name | Description |
| --- | --- |
| `config-path` | Path to the generated `mkdocs.yml`. |
| `requirements-path` | Path to the generated `requirements.txt`. |
| `overrides-path` | Path to the generated theme overrides directory. |

## Advanced

- Replaces the managed `mkdocs.yml`, `requirements.txt`, and `overrides/` contents on every run.
- Keeps the generated files together under `output-directory`.

## Examples

Configure MkDocs in an isolated directory:

```yaml
- name: Configure MkDocs
  id: mkdocs-config
  uses: athackst/ci/actions/mkdocs-config@main
  with:
    output-directory: ${{ runner.temp }}/mkdocs

- name: Install site dependencies
  shell: bash
  run: python3 -m pip install -r "${{ steps.mkdocs-config.outputs.requirements-path }}"

- name: Build docs
  shell: bash
  run: mkdocs build --config-file "${{ steps.mkdocs-config.outputs.config-path }}"
```

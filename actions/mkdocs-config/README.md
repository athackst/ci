# Configure Mkdocs for GitHub Pages

Copy the bundled MkDocs configuration into the workspace and append the required Python packages for the site.

## Usage

```yaml
- name: Configure MkDocs
  uses: athackst/ci/actions/mkdocs-config@main
```

## Advanced

- Copies the bundled `mkdocs.yml` into the workspace root.
- Copies the bundled `overrides/` directory into the workspace root.
- Creates `requirements.txt` if it does not already exist.
- Appends the action's bundled Python requirements to `requirements.txt`.
- Existing workspace files may be overwritten or extended by these copy operations.

## Examples

Configure MkDocs before building the site:

```yaml
- name: Configure MkDocs
  uses: athackst/ci/actions/mkdocs-config@main

- name: Install site dependencies
  shell: bash
  run: |
    python3 -m pip install -r requirements.txt

- name: Build docs
  shell: bash
  run: |
    mkdocs build
```

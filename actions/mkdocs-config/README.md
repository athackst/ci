# Configure MkDocs for GitHub Pages

Layer the bundled MkDocs site config into the workspace and append the required Python packages for the site.

## Usage

```yaml
- name: Configure MkDocs
  uses: athackst/ci/actions/mkdocs-config@main
```

## Advanced

- Layers the bundled `mkdocs.yml` into the workspace root as a base config.
- When the repository already has an `mkdocs.yml`, its keys override the bundled defaults.
- Copies the bundled `overrides/` directory into the workspace root.
- Creates `requirements.txt` if it does not already exist.
- Appends the action's bundled Python requirements to `requirements.txt`.
- Existing workspace files with the same names are merged or extended.

## Examples

Configure MkDocs before building the site:

```yaml
- name: Configure MkDocs
  uses: athackst/ci/actions/mkdocs-config@main

- name: Install site dependencies
  shell: bash
  run: python3 -m pip install -r requirements.txt

- name: Build docs
  shell: bash
  run: mkdocs build
```

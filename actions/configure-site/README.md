# Configure Site

Resolve normalized site location settings from explicit hosting values or GitHub Pages.

## Usage

```yaml
- name: Configure site
  id: site
  uses: athackst/ci/actions/configure-site@main
```

## Inputs

| Name | Description | Default |
| --- | --- | --- |
| `host` | Site host or origin, such as `docs.example.com` or `https://docs.example.com`. (optional) | `""` |
| `base-path` | Path beneath the site host, such as `/project`. (optional) | `""` |
| `base-url` | Full site base URL. Derived from `host` and `base-path` when omitted. (optional) | `""` |
| `version` | Version path appended to the site location, such as `dev` or `1.2.3`. (optional) | `""` |

## Outputs

| Name | Description |
| --- | --- |
| `host` | Normalized site host. |
| `base-path` | Normalized site base path. |
| `base-url` | Normalized site base URL. |
| `version` | Normalized version. |

## Permissions

GitHub Pages resolution uses `pages: read` on the caller job.

## Advanced

- An empty `host` resolves the site location with GitHub Pages.
- Explicit `base-path` and `base-url` values accompany an explicit `host`.
- A hostname defaults to `https`; explicit `http` and `https` schemes are preserved.
- A supplied `base-url` must share the normalized origin and path represented by `host` and `base-path`.
- `version` is normalized independently so build tooling can apply it where needed.

## Examples

Resolve an externally hosted, versioned site:

```yaml
- name: Configure site
  id: site
  uses: athackst/ci/actions/configure-site@main
  with:
    host: docs.example.com
    base-path: /project
    version: dev
```

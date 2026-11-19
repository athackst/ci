# Site

`site.yml` builds and optionally deploys documentation sites.

## Generated When

Generated when `site_generator` is `mkdocs` or `jekyll`.

Choose `site_generator: none` when an external provider owns the site workflow.

## Runs On

- Pushes to `main`
- Pull requests
- Release `published` events
- Manual requests (`workflow_dispatch`) on `main`

## Calls

For MkDocs:

```yaml
uses: athackst/ci/.github/workflows/mkdocs_site.yml@main
```

See [`mkdocs_site.yml`](../workflows/mkdocs_site.md) for the reusable workflow
contract.

For Jekyll:

```yaml
uses: athackst/ci/.github/workflows/jekyll_site.yml@main
```

See [`jekyll_site.yml`](../workflows/jekyll_site.md) for the reusable workflow
contract.

## Dependencies

```mermaid
flowchart TD
    template["Template workflow<br/>site.yml"]

    subgraph build_site["build-site (configured generator)"]
        direction LR

        subgraph mkdocs_option["MkDocs option"]
            mkdocs["Reusable workflow<br/>mkdocs_site.yml"]
            mkdocs --> configure_pages["Action<br/>actions/configure-pages"]
            mkdocs --> mkdocs_preset["Docker action<br/>mkdocs-preset"]
            mkdocs --> pages_build["Actions<br/>checkout, upload-pages-artifact"]
        end

        subgraph jekyll_option["Jekyll option"]
            jekyll["Reusable workflow<br/>jekyll_site.yml"]
            jekyll --> configure_pages
            jekyll --> jekyll_preset["Docker action<br/>jekyll-preset"]
            jekyll --> pages_jekyll["Actions<br/>checkout, upload-pages-artifact"]
        end
    end

    template --> mkdocs
    template --> jekyll
    mkdocs -->|artifact and outputs| test["Reusable workflow<br/>htmlproofer_site.yml"]
    jekyll -->|artifact and outputs| test
    mkdocs -->|artifact and outputs| deploy["Reusable workflow<br/>deploy_site.yml"]
    jekyll -->|artifact and outputs| deploy

    test --> cache["Composite action<br/>htmlproofer-cache"]
    test --> test_artifact["Actions<br/>checkout, download-artifact"]
    cache --> htmlproofer["Action<br/>athackst/htmlproofer-action"]
    cache --> cache_actions["Actions<br/>cache/restore, cache/save"]
    deploy --> pages_deploy["Actions<br/>configure-pages, deploy-pages,<br/>checkout, download-artifact"]
    deploy --> versite["Action<br/>PrimerPages/versite"]
    deploy -->|release preparation succeeds| dispatch["site.yml<br/>request-main-deployment"]
    dispatch -->|workflow_dispatch on main| template

    classDef template fill:#e0f2fe,stroke:#0284c7
    classDef workflow fill:#ede9fe,stroke:#7c3aed
    classDef action fill:#ecfccb,stroke:#65a30d
    class template template
    class mkdocs,jekyll,test,deploy workflow
    class configure_pages,mkdocs_preset,mkdocs_plugin,pages_build,jekyll_preset,pages_jekyll,cache,test_artifact,htmlproofer,cache_actions,pages_deploy,versite action
```

## Permissions

- `build-site`: `contents: read`, plus `pages: read` for GitHub Pages location resolution
- `test-site`: `contents: read`
- `deploy-site`: `contents: write`, `pages: write`, `id-token: write`
- `request-main-deployment`: `actions: write` to dispatch Site on `main` after release preparation succeeds

## Behavior

- On pull requests, builds the configured site and runs HTMLProofer without deploying.
- On `main` pushes and manual requests, builds and deploys the configured site.
- `build-site` is responsible for building the site artifact and exposing the site metadata used by `test-site` and `deploy-site`.
- `test-site` runs HTMLProofer against the built artifact and reports link failures without blocking deployment.
- When releases are enabled, both MkDocs and Jekyll publish versioned docs: `main` publishes `dev`, and release events publish the release tag plus `latest`.
- `deploy-site` handles the publish step:
  - non-versioned sites deploy the built artifact with GitHub Pages actions
  - versioned sites update `gh-pages` with `PrimerPages/versite`, then deploy the complete branch through GitHub Pages Actions
  - release runs update their version and `latest` alias without deploying from the tag
  - `dry-run` disables the publish step for either deployment mode

`request-main-deployment` runs in `site.yml` after `deploy-site` succeeds on a published release. It dispatches Site on `main`, without waiting for HTMLProofer. The dispatched main build updates `dev`, preserves release history and the `latest` default, and deploys the complete site. Unversioned release runs dispatch a main rebuild without retaining the tagged site.

Set the Pages source to **GitHub Actions** and allow `main` in the `github-pages` environment. Release tags do not need environment access. Check the dispatched Site run for the deployment result; retry it with **Run workflow** on `main` if needed.

The reusable deployment workflow queues version updates and publication together. Site queues whole production runs, including builds, so an older main build cannot publish after a newer build. The queue retains up to 100 pending runs, including main builds dispatched by releases. PR runs stay outside the production queue; newer PR build and HTMLProofer jobs cancel older jobs of the same kind for that PR. HTMLProofer remains independent and does not block version updates, dispatch, or deployment.

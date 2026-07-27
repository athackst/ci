from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ACTION_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ACTION_DIR))

import render_mkdocs_config  # noqa: E402


class RenderMkdocsConfigTests(unittest.TestCase):
    """Verify deterministic rendering of the managed MkDocs config."""

    def test_render_yaml_template_substitutes_all_values(self):
        rendered = render_mkdocs_config.render_yaml_template(
            ACTION_DIR / "mkdocs.yml",
            {
                "docs_dir": "/github/workspace/docs",
                "site_dir": "/github/workspace/site",
                "overrides_dir": "/workspace/mkdocs/overrides",
                "site_name": "Docs $100: \"Example\"",
                "repo_url": "https://github.com/example/repo",
                "site_url": "https://example.github.io/repo/",
                "edit_uri": "edit/main/",
            },
        )

        self.assertIn('site_name: "Docs $100: \\\"Example\\\""', rendered)
        self.assertIn('docs_dir: "/github/workspace/docs"', rendered)
        self.assertIn('site_dir: "/github/workspace/site"', rendered)
        self.assertIn('custom_dir: "/workspace/mkdocs/overrides"', rendered)
        self.assertNotIn("${", rendered)

    def test_main_writes_rendered_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_config = Path(temp_dir) / "mkdocs.yml"
            argv = [
                "--template",
                str(ACTION_DIR / "mkdocs.yml"),
                "--output",
                str(output_config),
                "--docs-dir",
                "/github/workspace/docs",
                "--site-dir",
                "/github/workspace/site",
                "--overrides-dir",
                "/workspace/mkdocs/overrides",
                "--site-name",
                "CI Test Site",
                "--repo-url",
                "https://github.com/athackst/ci",
                "--site-url",
                "",
                "--edit-uri",
                "edit/main/",
            ]
            with mock.patch.object(
                sys, "argv", ["render_mkdocs_config.py", *argv]
            ):
                exit_code = render_mkdocs_config.main()

            self.assertEqual(exit_code, 0)
            rendered = output_config.read_text(encoding="utf-8")
            self.assertIn('site_name: "CI Test Site"', rendered)
            self.assertNotIn("${", rendered)

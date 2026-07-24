from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

import sys

ACTION_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ACTION_DIR))

import render_jekyll_config  # noqa: E402


class RenderJekyllConfigTests(unittest.TestCase):
    """Verify deterministic rendering of the managed Jekyll config."""
    def render_versions_config(self, versions_config: str = "") -> dict[str, object]:
        with mock.patch.dict(
            os.environ,
            {
                "TITLE": "CI Test Site",
                "DESCRIPTION": "Test description",
                "IMAGE": "",
                "EDIT_URL": "https://example.com/edit/",
                "REPOSITORY": "athackst/ci",
                "NAV_FILENAME": ".nav.yml",
                "VERSIONS_ENABLED": "true" if versions_config else "false",
                "VERSIONS_CONFIG": versions_config,
                "PREFIX": "/ci",
            },
            clear=False,
        ):
            rendered = render_jekyll_config.render_yaml_template(ACTION_DIR / "_config.yml")

        return rendered["versions"]

    def test_render_yaml_template_versions_disabled_by_default(self):
        versions = self.render_versions_config()
        self.assertIs(versions["enabled"], False)
        self.assertEqual(versions["config"], "")

    def test_render_yaml_template_versions_enabled_with_custom_config(self):
        versions = self.render_versions_config("ci/versions.json")
        self.assertIs(versions["enabled"], True)
        self.assertEqual(versions["config"], "ci/versions.json")

    def test_main_writes_versions_flag_and_config_path(self):
        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.dict(
            os.environ,
            {
                "TITLE": "CI Test Site",
                "DESCRIPTION": "Test description",
                "IMAGE": "",
                "EDIT_URL": "https://example.com/edit/",
                "REPOSITORY": "athackst/ci",
                "NAV_FILENAME": ".nav.yml",
                "VERSIONS_ENABLED": "true",
                "VERSIONS_CONFIG": "docs/versions.json",
                "PREFIX": "/ci",
            },
            clear=False,
        ):
            output_config = Path(temp_dir) / "_config.yml"
            output_config.write_text("repository_only: true\n", encoding="utf-8")

            argv = [str(ACTION_DIR / "_config.yml"), str(output_config)]
            with mock.patch.object(sys, "argv", ["render_jekyll_config.py", *argv]):
                exit_code = render_jekyll_config.main()

            self.assertEqual(exit_code, 0)
            rendered = yaml.safe_load(output_config.read_text(encoding="utf-8"))
            self.assertIs(rendered["versions"]["enabled"], True)
            self.assertEqual(rendered["versions"]["config"], "docs/versions.json")
            self.assertNotIn("repository_only", rendered)

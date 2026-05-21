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

import merge_jekyll_config  # noqa: E402


class MergeJekyllConfigTests(unittest.TestCase):
    def render_versions_config(self, versions_enabled: str, prefix: str = "ci") -> dict[str, object]:
        with mock.patch.dict(
            os.environ,
            {
                "TITLE": "CI Test Site",
                "DESCRIPTION": "Test description",
                "IMAGE": "",
                "EDIT_URL": "https://example.com/edit/",
                "REPOSITORY": "athackst/ci",
                "VERSIONS_ENABLED": versions_enabled,
                "PREFIX": prefix,
            },
            clear=False,
        ):
            rendered = merge_jekyll_config.render_yaml_template(ACTION_DIR / "_config.yml")

        return rendered["versions"]

    def test_render_yaml_template_versions_disabled_is_boolean_false(self):
        versions = self.render_versions_config("false")
        self.assertIs(versions["enabled"], False)
        self.assertEqual(versions["prefix"], "ci")

    def test_render_yaml_template_versions_enabled_is_boolean_true(self):
        versions = self.render_versions_config("true", prefix="docs")
        self.assertIs(versions["enabled"], True)
        self.assertEqual(versions["prefix"], "docs")

    def test_main_writes_versions_flag_and_prefix(self):
        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.dict(
            os.environ,
            {
                "TITLE": "CI Test Site",
                "DESCRIPTION": "Test description",
                "IMAGE": "",
                "EDIT_URL": "https://example.com/edit/",
                "REPOSITORY": "athackst/ci",
                "VERSIONS_ENABLED": "true",
                "PREFIX": "ci",
            },
            clear=False,
        ):
            local_config = Path(temp_dir) / "_config.yml"
            local_config.write_text("", encoding="utf-8")

            argv = [str(ACTION_DIR / "_config.yml"), str(local_config)]
            with mock.patch.object(sys, "argv", ["merge_jekyll_config.py", *argv]):
                exit_code = merge_jekyll_config.main()

            self.assertEqual(exit_code, 0)
            merged = yaml.safe_load(local_config.read_text(encoding="utf-8"))
            self.assertIs(merged["versions"]["enabled"], True)
            self.assertEqual(merged["versions"]["prefix"], "ci")

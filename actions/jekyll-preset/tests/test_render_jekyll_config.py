from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ACTION_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ACTION_DIR))

import render_jekyll_config  # noqa: E402


class RenderJekyllConfigTests(unittest.TestCase):
    def test_render_yaml_template_omits_empty_image_and_versions(self) -> None:
        rendered = render_jekyll_config.render_yaml_template(
            ACTION_DIR / "_config.yml",
            {
                "title": "CI Test Site",
                "description": "Test description",
                "image": "",
                "edit_url": "https://example.com/edit/",
                "repository": "athackst/ci",
                "nav_filename": ".nav.yml",
                "versions_config": "",
                "base_path": "/ci",
            },
        )

        self.assertEqual(rendered["title"], "CI Test Site")
        self.assertNotIn("image", rendered)
        self.assertFalse(rendered["versions"]["enabled"])
        self.assertEqual(rendered["versions"]["config"], "")
        self.assertEqual(rendered["versions"]["prefix"], "/ci")

    def test_main_writes_enabled_versions_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "_config.yml"
            argv = [
                "render_jekyll_config.py",
                "--template",
                str(ACTION_DIR / "_config.yml"),
                "--output",
                str(output_path),
                "--title",
                "CI Test Site",
                "--description",
                "Test description",
                "--image",
                "https://example.com/image.png",
                "--edit-url",
                "https://example.com/edit/",
                "--repository",
                "athackst/ci",
                "--nav-filename",
                ".nav.yml",
                "--versions-config",
                "/ci/versions.json",
                "--base-path",
                "/ci",
            ]

            with mock.patch.object(sys, "argv", argv):
                exit_code = render_jekyll_config.main()

            rendered = output_path.read_text(encoding="utf-8")
            self.assertEqual(exit_code, 0)
            self.assertIn("enabled: true", rendered)
            self.assertIn("config: /ci/versions.json", rendered)
            self.assertIn("image: https://example.com/image.png", rendered)


if __name__ == "__main__":
    unittest.main()

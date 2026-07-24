import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "resolve_site_settings.py"
SPEC = importlib.util.spec_from_file_location("resolve_site_settings", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ResolveSiteSettingsTests(unittest.TestCase):
    def test_normalizes_hostname_and_paths(self) -> None:
        settings = MODULE.resolve_site_settings(
            host="docs.example.com/",
            base_path="project/",
            version="/dev/",
        )

        self.assertEqual(settings["host"], "docs.example.com")
        self.assertEqual(settings["base_path"], "/project")
        self.assertEqual(settings["base_url"], "https://docs.example.com/project")
        self.assertEqual(settings["version"], "dev")

    def test_preserves_explicit_http_origin(self) -> None:
        settings = MODULE.resolve_site_settings(host="http://localhost:4000")

        self.assertEqual(settings["host"], "localhost:4000")
        self.assertEqual(settings["base_url"], "http://localhost:4000")

    def test_derives_path_from_base_url(self) -> None:
        settings = MODULE.resolve_site_settings(
            host="https://docs.example.com",
            base_url="https://docs.example.com/project/",
        )

        self.assertEqual(settings["base_path"], "/project")
        self.assertEqual(settings["base_url"], "https://docs.example.com/project")

    def test_rejects_mismatched_base_url_origin(self) -> None:
        with self.assertRaisesRegex(ValueError, "origin must match"):
            MODULE.resolve_site_settings(
                host="docs.example.com",
                base_url="https://other.example.com/project",
            )

    def test_rejects_mismatched_base_url_path(self) -> None:
        with self.assertRaisesRegex(ValueError, "path must match"):
            MODULE.resolve_site_settings(
                host="docs.example.com",
                base_path="/one",
                base_url="https://docs.example.com/two",
            )

    def test_empty_path_and_version_remain_empty(self) -> None:
        settings = MODULE.resolve_site_settings(host="docs.example.com")

        self.assertEqual(settings["base_path"], "")
        self.assertEqual(settings["version"], "")


if __name__ == "__main__":
    unittest.main()

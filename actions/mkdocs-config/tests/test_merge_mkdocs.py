import tempfile
import unittest
from pathlib import Path
import sys

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from merge_mkdocs import MkdocsConfigLoader, main, merge_values  # noqa: E402


class TestMergeMkdocs(unittest.TestCase):
    def run_main(self, base_path: Path, local_path: Path) -> None:
        argv = sys.argv
        try:
            sys.argv = ["merge_mkdocs.py", str(base_path), str(local_path)]
            self.assertEqual(main(), 0)
        finally:
            sys.argv = argv

    def test_merge_values_recursively_merges_dicts(self) -> None:
        base = {
            "theme": {
                "name": "material",
                "features": ["search.share"],
                "palette": {"primary": "green", "accent": "green"},
            },
            "plugins": ["simple", "search"],
        }
        override = {
            "theme": {
                "features": ["content.action.edit"],
                "palette": {"accent": "blue"},
            },
            "plugins": ["tags", "search"],
        }

        merged = merge_values(base, override)

        self.assertEqual(
            merged,
            {
                "theme": {
                    "name": "material",
                    "features": ["content.action.edit"],
                    "palette": {"primary": "green", "accent": "blue"},
                },
                "plugins": ["tags", "search"],
            },
        )

    def test_main_preserves_empty_repo_url_override(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            base_path = temp_path / "base.yml"
            local_path = temp_path / "mkdocs.yml"

            base_path.write_text(
                yaml.safe_dump(
                    {
                        "plugins": ["simple", "search"],
                        "repo_url": "https://github.com/example/project",
                        "theme": {"name": "material", "features": ["search.share"]},
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            local_path.write_text(
                yaml.safe_dump(
                    {
                        "plugins": ["tags", "search"],
                        "repo_url": "",
                        "theme": {"features": ["content.action.edit"]},
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            self.run_main(base_path, local_path)

            merged = yaml.safe_load(local_path.read_text(encoding="utf-8"))
            self.assertEqual(merged["repo_url"], "")
            self.assertEqual(merged["plugins"], ["tags", "search"])
            self.assertEqual(merged["theme"]["name"], "material")
            self.assertEqual(merged["theme"]["features"], ["content.action.edit"])

    def test_main_uses_base_config_when_local_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            base_path = temp_path / "base.yml"
            local_path = temp_path / "mkdocs.yml"

            base_path.write_text(
                yaml.safe_dump(
                    {
                        "site_name": "base-site",
                        "plugins": ["simple", "search"],
                        "theme": {"name": "material"},
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            self.run_main(base_path, local_path)

            merged = yaml.safe_load(local_path.read_text(encoding="utf-8"))
            self.assertEqual(merged["site_name"], "base-site")
            self.assertEqual(merged["plugins"], ["simple", "search"])
            self.assertEqual(merged["theme"]["name"], "material")

    def test_main_replaces_lists_instead_of_appending(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            base_path = temp_path / "base.yml"
            local_path = temp_path / "mkdocs.yml"

            base_path.write_text(
                yaml.safe_dump(
                    {
                        "plugins": ["simple", "search"],
                        "theme": {"features": ["search.share", "search.suggest"]},
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )
            local_path.write_text(
                yaml.safe_dump(
                    {
                        "plugins": ["tags", "search"],
                        "theme": {"features": ["content.action.edit"]},
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            self.run_main(base_path, local_path)

            merged = yaml.safe_load(local_path.read_text(encoding="utf-8"))
            self.assertEqual(merged["plugins"], ["tags", "search"])
            self.assertEqual(merged["theme"]["features"], ["content.action.edit"])

    def test_loader_preserves_unknown_tags(self) -> None:
        loaded = yaml.load(
            "emoji_index: !!python/name:pymdownx.emoji.gemoji ''\n",
            Loader=MkdocsConfigLoader,
        )

        self.assertEqual(loaded["emoji_index"].tag, "tag:yaml.org,2002:python/name:pymdownx.emoji.gemoji")

    def test_main_preserves_tagged_values_from_real_base_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            base_path = Path(__file__).resolve().parents[1] / "mkdocs.yml"
            local_path = temp_path / "mkdocs.yml"

            local_path.write_text(
                yaml.safe_dump(
                    {
                        "site_name": "cookbook",
                        "repo_url": "",
                    },
                    sort_keys=False,
                ),
                encoding="utf-8",
            )

            self.run_main(base_path, local_path)

            merged_text = local_path.read_text(encoding="utf-8")
            self.assertIn("!!python/name:pymdownx.emoji.gemoji", merged_text)
            self.assertIn("!!python/name:pymdownx.emoji.to_png", merged_text)
            self.assertIn("repo_url: ''", merged_text)

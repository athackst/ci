from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "resolve_labeler_config.py"


class ResolveLabelerConfigTests(unittest.TestCase):
    def run_resolver(self, configuration):
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            config_path = directory_path / "config.yml"
            output_path = directory_path / "flattened.yml"
            config_path.write_text(configuration, encoding="utf-8")

            result = subprocess.run(
                [
                    "python3",
                    str(SCRIPT_PATH),
                    "--config-path",
                    str(config_path),
                    "--output-path",
                    str(output_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            flattened = None
            if output_path.exists():
                flattened = yaml.safe_load(output_path.read_text(encoding="utf-8"))
            return result, flattened

    def test_extracts_labels_from_combined_ci_config(self):
        result, flattened = self.run_resolver(
            """
name-template: Release v$RESOLVED_VERSION
labels:
  bug:
    - head-branch: ["^bug"]
    - description: Bug fixes
    - color: "d73a4a"
"""
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            flattened,
            {
                "bug": [
                    {"head-branch": ["^bug"]},
                    {"description": "Bug fixes"},
                    {"color": "d73a4a"},
                ]
            },
        )

    def test_accepts_flattened_label_config(self):
        result, flattened = self.run_resolver(
            """
bug:
  - description: Bug fixes
  - color: d73a4a
"""
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            flattened,
            {"bug": [{"description": "Bug fixes"}, {"color": "d73a4a"}]},
        )

    def test_rejects_unknown_labeler_conditions(self):
        result, flattened = self.run_resolver(
            """
labels:
  bug:
    - unknown-condition: true
"""
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIsNone(flattened)
        self.assertIn("schema validation failed", result.stderr)


if __name__ == "__main__":
    unittest.main()

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from get_expected_labels import ConfigError, compute_expected_labels

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "get_expected_labels.py"
REPO_ROOT = Path(__file__).resolve().parents[3]


class GetExpectedLabelsTests(unittest.TestCase):
    def write_config(self, content):
        handle = tempfile.NamedTemporaryFile(
            mode="w", suffix=".yml", delete=False, encoding="utf-8"
        )
        self.addCleanup(os.unlink, handle.name)
        handle.write(content)
        handle.close()
        return Path(handle.name)

    def expected(self, content, head_ref, base_ref=""):
        return compute_expected_labels(self.write_config(content), head_ref, base_ref)

    def test_head_branch_patterns_are_regexes(self):
        config = """
labels:
  bug:
    - head-branch: ['^fix', '^bug']
    - description: "Something isn't working"
"""
        self.assertEqual(self.expected(config, "fix/oops"), ["bug"])
        self.assertEqual(self.expected(config, "hotfix/oops"), [])

    def test_unanchored_pattern_uses_partial_match(self):
        config = "docs:\n  - head-branch: ['doc']\n"
        self.assertEqual(self.expected(config, "update-docs"), ["docs"])

    def test_flat_config_without_labels_key(self):
        config = "bug:\n  - head-branch: ['^fix']\n"
        self.assertEqual(self.expected(config, "fix/oops"), ["bug"])

    def test_unquoted_glob_flow_list_parses(self):
        # The previous parser used ast.literal_eval and silently dropped
        # patterns that were not valid Python literals, such as these.
        config = "maintenance:\n  - head-branch: [^chore, ^maint]\n"
        self.assertEqual(self.expected(config, "chore/tidy"), ["maintenance"])

    def test_universal_changed_files_glob_is_guaranteed(self):
        config = """
labels:
  test-label:
    - changed-files:
      - any-glob-to-any-file: ["**"]
    - description: "This is just a test"
    - color: "cfd3d7"
"""
        self.assertEqual(self.expected(config, "any-branch"), ["test-label"])

    def test_narrow_changed_files_glob_is_not_guaranteed(self):
        config = """
docs:
  - changed-files:
    - any-glob-to-any-file: ["**/*.md"]
"""
        self.assertEqual(self.expected(config, "any-branch"), [])

    def test_top_level_conditions_are_ored(self):
        config = """
maintenance:
  - head-branch: ['^chore']
  - changed-files:
    - any-glob-to-any-file: [".github/**"]
"""
        self.assertEqual(self.expected(config, "chore/tidy"), ["maintenance"])
        self.assertEqual(self.expected(config, "feature/tidy"), [])

    def test_keys_within_one_condition_are_anded(self):
        config = "release:\n  - head-branch: ['^release']\n    base-branch: ['^main$']\n"
        self.assertEqual(self.expected(config, "release/1.0", "main"), ["release"])
        self.assertEqual(self.expected(config, "release/1.0", "develop"), [])

    def test_metadata_only_labels_are_not_expected(self):
        config = """
question:
  - description: "Further information is requested"
  - color: "#7e22ce"
"""
        self.assertEqual(self.expected(config, "fix/oops"), [])

    def test_invalid_regex_is_an_error(self):
        config = "bad:\n  - head-branch: ['[unclosed']\n"
        with self.assertRaises(ConfigError):
            self.expected(config, "fix/oops")

    def test_repo_fixture_yields_its_label(self):
        fixture = REPO_ROOT / "tests" / "fixtures" / "test-labeler.yml"
        self.assertEqual(
            compute_expected_labels(fixture, "any-branch", ""), ["test-label"]
        )

    def test_repo_ci_config_matches_branch_rules(self):
        config = REPO_ROOT / ".github" / "ci-config.yml"
        self.assertEqual(
            compute_expected_labels(config, "fix/expected-labels", ""), ["bug"]
        )

    def test_cli_requires_head_ref(self):
        config = self.write_config("bug:\n  - head-branch: ['^fix']\n")
        env = {key: value for key, value in os.environ.items() if key != "GITHUB_HEAD_REF"}
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), str(config)],
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("GITHUB_HEAD_REF", result.stderr)

    def test_cli_emits_json(self):
        config = self.write_config("bug:\n  - head-branch: ['^fix']\n")
        env = dict(os.environ, GITHUB_HEAD_REF="fix/oops")
        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH), str(config)],
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout), ["bug"])


if __name__ == "__main__":
    unittest.main()

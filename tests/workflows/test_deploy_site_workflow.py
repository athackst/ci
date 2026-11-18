from pathlib import Path
import os
import subprocess
import tempfile
import unittest

import yaml


WORKFLOW_PATH = (
    Path(__file__).resolve().parents[2]
    / ".github"
    / "workflows"
    / "deploy_site.yml"
)


class DeploySiteWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
        cls.jobs = cls.workflow["jobs"]

    def test_action_deploy_waits_for_preparation_and_handles_unversioned_skip(self):
        job = self.jobs["deploy-action"]
        condition = job["if"]
        self.assertEqual(job["needs"], "prepare-versioned")
        self.assertIn("!inputs.dry-run", condition)
        self.assertIn("!cancelled()", condition)
        self.assertIn("needs.prepare-versioned.result == 'success'", condition)
        self.assertIn("inputs.version == '' || needs.prepare-versioned.result == 'success'", condition)
        self.assertNotIn("always()", condition)

    def test_prepare_versions_without_pushing_dry_runs(self):
        job = self.jobs["prepare-versioned"]
        self.assertEqual(job["if"], "${{ inputs.version != '' }}")
        versite_step = next(step for step in job["steps"] if step.get("uses") == "PrimerPages/versite@main")
        self.assertEqual(versite_step["with"]["push"], "${{ !inputs.dry-run }}")

    def test_only_deployment_configures_pages_with_permissions_scoped_per_job(self):
        preparation = self.jobs["prepare-versioned"]
        deployment = self.jobs["deploy-action"]
        self.assertEqual(preparation["permissions"], {"contents": "write"})
        self.assertEqual(deployment["permissions"], {"pages": "write", "id-token": "write"})
        self.assertFalse(any(step.get("uses") == "actions/configure-pages@v6" for step in preparation["steps"]))
        self.assertTrue(any(step.get("uses") == "actions/configure-pages@v6" for step in deployment["steps"]))

    def test_complete_artifact_has_distinct_name_and_is_used_for_deployment(self):
        upload = next(step for step in self.jobs["prepare-versioned"]["steps"] if step.get("uses") == "actions/upload-pages-artifact@v5")
        deploy = next(step for step in self.jobs["deploy-action"]["steps"] if step.get("uses") == "actions/deploy-pages@v5")
        self.assertNotIn("if", upload)
        self.assertEqual(upload["with"]["name"], "versioned-${{ inputs.artifact-name }}")
        self.assertEqual(upload["with"]["path"], "${{ runner.temp }}/versioned-site")
        self.assertEqual(deploy["with"]["artifact_name"], "${{ inputs.version != '' && format('versioned-{0}', inputs.artifact-name) || inputs.artifact-name }}")

    def test_legacy_type_only_controls_deprecation_warnings(self):
        workflow = yaml.safe_load(WORKFLOW_PATH.read_text())
        inputs = workflow.get("on", workflow.get(True))["workflow_call"]["inputs"]
        self.assertEqual(inputs["type"]["default"], "")
        for job in self.jobs.values():
            self.assertNotIn("inputs.type", job.get("if", ""))
            for step in job.get("steps", []):
                if step.get("name") == "Warn about deprecated type input":
                    self.assertIn("inputs.type != ''", step["if"])
                    result = subprocess.run(["bash", "-c", step["run"]], capture_output=True, text=True, check=True)
                    self.assertIn("::warning::", result.stdout)
                    self.assertIn("deprecated and ignored", result.stdout)
                else:
                    self.assertNotIn("inputs.type", yaml.safe_dump(step))
        export = next(step for step in self.jobs["prepare-versioned"]["steps"] if step.get("name") == "Export versioned site")
        self.assertNotIn("if", export)

    def test_deployments_are_serialized(self):
        self.assertEqual(self.workflow["concurrency"], {
            "group": "site-deployment-${{ github.repository }}",
            "cancel-in-progress": False,
        })

    def test_export_contains_all_versions_aliases_metadata_and_no_source_tree(self):
        export = next(step for step in self.jobs["prepare-versioned"]["steps"] if step.get("name") == "Export versioned site")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            repo.mkdir()

            def git(*args):
                return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)

            git("init", "-b", "gh-pages")
            git("config", "user.name", "Workflow Test")
            git("config", "user.email", "workflow@example.com")
            for name, text in {
                "v1.0.0/index.html": "Older release",
                "v2.0.0/index.html": "New release",
                "dev/index.html": "Development",
                "latest/index.html": "Redirect to v2.0.0",
                "index.html": "Redirect to latest",
                "versions.json": '[{"version": "v1.0.0"}, {"version": "v2.0.0"}]',
                ".nojekyll": "",
                "CNAME": "docs.example.com",
            }.items():
                path = repo / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text)
            git("add", ".")
            git("commit", "-m", "Published versions")
            git("checkout", "--orphan", "main")
            git("rm", "-rf", ".")
            (repo / "source-only.txt").write_text("Must not be published")
            git("add", ".")
            git("commit", "-m", "Source")
            subprocess.run(["bash", "-c", export["run"]], cwd=repo, env={**os.environ, "BRANCH": "gh-pages", "RUNNER_TEMP": str(root)}, check=True)
            site = root / "versioned-site"
            for version in ("v1.0.0", "v2.0.0", "dev", "latest"):
                self.assertTrue((site / version / "index.html").is_file())
            self.assertEqual((site / "v1.0.0/index.html").read_text(), "Older release")
            self.assertTrue((site / "versions.json").is_file())
            self.assertTrue((site / "index.html").is_file())
            self.assertTrue((site / ".nojekyll").is_file())
            self.assertEqual((site / "CNAME").read_text(), "docs.example.com")
            self.assertFalse((site / ".git").exists())
            self.assertFalse((site / "source-only.txt").exists())
            self.assertEqual(git("branch", "--show-current").stdout.strip(), "main")


if __name__ == "__main__":
    unittest.main()

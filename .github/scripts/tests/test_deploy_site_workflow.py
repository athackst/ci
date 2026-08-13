from pathlib import Path
import unittest

import yaml


WORKFLOW_PATH = Path(__file__).resolve().parents[2] / "workflows" / "deploy_site.yml"


class DeploySiteWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
        cls.jobs = workflow["jobs"]

    def test_action_deploy_uses_typed_dry_run_input(self):
        condition = self.jobs["deploy-action"]["if"]

        self.assertEqual(
            condition,
            "${{ !inputs.dry-run && inputs.type == 'action' && inputs.version == '' }}",
        )

    def test_branch_deploy_uses_typed_dry_run_input(self):
        versite_step = next(
            step
            for step in self.jobs["deploy-branch"]["steps"]
            if step.get("uses") == "PrimerPages/versite@main"
        )

        self.assertEqual(versite_step["with"]["push"], "${{ !inputs.dry-run }}")


if __name__ == "__main__":
    unittest.main()

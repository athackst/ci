from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "copier/template/.github/workflows/[% if site_generator != 'none' %]site.yml[% endif %].jinja"


class SiteWorkflowTests(unittest.TestCase):
    def test_site_workflows_allow_manual_deployment_only_from_main(self):
        local = yaml.safe_load((ROOT / ".github/workflows/site.yml").read_text())
        template_condition = TEMPLATE.read_text().split("  deploy-site:\n", 1)[1].split("    needs:", 1)[0]
        conditions = [local["jobs"]["deploy-site"]["if"], yaml.safe_load(template_condition)["if"]]
        cases = [
            ("workflow_dispatch", "refs/heads/main", "", True),
            ("workflow_dispatch", "refs/heads/feature", "", False),
            ("workflow_dispatch", "refs/tags/v2.2.1", "", False),
            ("push", "refs/heads/main", "", True),
            ("push", "refs/heads/feature", "", False),
            ("pull_request", "refs/heads/main", "", False),
            ("pull_request", "refs/pull/1/merge", "", False),
            ("release", "refs/tags/v2.2.1", "published", True),
            ("release", "refs/tags/v2.2.1", "edited", False),
        ]
        for expression in conditions:
            expression = " ".join(expression.removeprefix("${{").removesuffix("}}").split())
            for event, ref, action, expected in cases:
                with self.subTest(event=event, ref=ref, action=action):
                    # Evaluate the workflow's boolean comparisons with fixed test inputs.
                    condition = expression.replace("github.event_name", repr(event))
                    condition = condition.replace("github.event.action", repr(action))
                    condition = condition.replace("github.ref", repr(ref))
                    condition = condition.replace("&&", " and ").replace("||", " or ")
                    self.assertEqual(eval(condition, {"__builtins__": {}}), expected)


if __name__ == "__main__":
    unittest.main()

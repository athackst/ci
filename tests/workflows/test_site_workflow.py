from pathlib import Path
import unittest
import os
import subprocess
import tempfile

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

    def test_htmlproofer_does_not_block_publication(self):
        local = yaml.safe_load((ROOT / ".github/workflows/site.yml").read_text())
        template_job = yaml.safe_load(TEMPLATE.read_text().split("  deploy-site:\n", 1)[1].split("    uses:", 1)[0])
        for job in [local["jobs"]["deploy-site"], template_job]:
            self.assertEqual(job["needs"], "build-site")
            self.assertNotIn("actions", job["permissions"])
        self.assertEqual(local["jobs"]["test-site"]["needs"], "build-site")

    def test_whole_production_runs_share_a_queue_before_builds_start(self):
        def value(expression, event, run_id, pr_number=1):
            if not isinstance(expression, str):
                return expression
            expr = expression.removeprefix("${{").removesuffix("}}")
            for key, item in {"github.event_name": event, "github.run_id": run_id, "github.event.pull_request.number": pr_number}.items():
                expr = expr.replace(key, repr(item))
            expr = expr.replace("&&", " and ").replace("||", " or ")
            return eval(expr, {"__builtins__": {}, "format": lambda pattern, *args: pattern.format(*args)})

        for text in [(ROOT / ".github/workflows/site.yml").read_text(), TEMPLATE.read_text()]:
            concurrency = yaml.safe_load(text.split("jobs:", 1)[0])["concurrency"]
            # Lock the complete workflow, rather than just publication after parallel builds.
            self.assertEqual(concurrency["queue"], "max")
            self.assertIs(concurrency["cancel-in-progress"], False)
            production = [value(concurrency["group"], event, run_id) for event, run_id in [("push", 1), ("push", 2), ("push", 3), ("release", 4), ("workflow_dispatch", 5)]]
            self.assertEqual(len(set(production)), 1)
            pr_runs = [value(concurrency["group"], "pull_request", run_id) for run_id in (6, 7)]
            self.assertEqual(len(set(production + pr_runs)), 3)
            pr_job_groups = []
            for job_name in ("build-site", "test-site"):
                job_prefix = text.split(f"  {job_name}:\n", 1)[1].split("    permissions:", 1)[0]
                job_concurrency = yaml.safe_load(job_prefix)["concurrency"]
                old_pr = value(job_concurrency["group"], "pull_request", 6)
                new_pr = value(job_concurrency["group"], "pull_request", 7)
                self.assertEqual(old_pr, new_pr)
                self.assertNotEqual(old_pr, value(job_concurrency["group"], "pull_request", 8, pr_number=2))
                self.assertTrue(value(job_concurrency["cancel-in-progress"], "pull_request", 7))
                self.assertFalse(value(job_concurrency["cancel-in-progress"], "push", 1))
                self.assertNotEqual(value(job_concurrency["group"], "push", 1), value(job_concurrency["group"], "push", 2))
                pr_job_groups.append(old_pr)
            self.assertEqual(len(set(pr_job_groups)), 2)

    def test_release_dispatch_depends_on_successful_preparation_without_waiting_for_htmlproofer(self):
        for text in [(ROOT / ".github/workflows/site.yml").read_text(), TEMPLATE.read_text()]:
            job = yaml.safe_load(text.split("  request-main-deployment:\n", 1)[1])
            self.assertEqual(job["needs"], "deploy-site")
            self.assertEqual(job["permissions"], {"actions": "write"})
            # The implicit success() condition prevents dispatch after failed/skipped preparation.
            self.assertNotIn("always()", job["if"])
            self.assertNotIn("!cancelled()", job["if"])
            condition = job["if"].removeprefix("${{").removesuffix("}}")
            for event, action, expected in [("release", "published", True), ("release", "edited", False), ("push", "", False), ("workflow_dispatch", "", False), ("pull_request", "", False)]:
                expr = condition.replace("github.event_name", repr(event)).replace("github.event.action", repr(action)).replace("&&", " and ")
                self.assertEqual(bool(eval(expr, {"__builtins__": {}})), expected)
            step = job["steps"][0]
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                gh = root / "gh"
                gh.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$CAPTURE"\n')
                gh.chmod(0o755)
                subprocess.run(["bash", "-c", step["run"]], check=True, env={**os.environ, "PATH": f"{root}:{os.environ['PATH']}", "CAPTURE": str(root / "args"), "GITHUB_REPOSITORY": "owner/site"})
                self.assertEqual((root / "args").read_text().splitlines(), ["workflow", "run", "site.yml", "--repo", "owner/site", "--ref", "main"])


if __name__ == "__main__":
    unittest.main()

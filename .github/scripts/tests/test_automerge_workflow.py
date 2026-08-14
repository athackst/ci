from pathlib import Path
import unittest

import yaml


WORKFLOW_PATH = Path(__file__).resolve().parents[2] / "workflows" / "automerge.yml"
CALLER_PATH = Path(__file__).resolve().parents[2] / "workflows" / "pr_automerge.yml"
TEMPLATE_CALLER_PATH = (
    Path(__file__).resolve().parents[2]
    / ".."
    / "copier"
    / "template"
    / ".github"
    / "workflows"
    / "pr_automerge.yml.jinja"
)


class AutomergeWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
        cls.jobs = workflow["jobs"]
        cls.caller = yaml.safe_load(CALLER_PATH.read_text(encoding="utf-8"))
        cls.caller_template = TEMPLATE_CALLER_PATH.read_text(encoding="utf-8")

    def step(self, job_id, step_id):
        return next(
            step
            for step in self.jobs[job_id]["steps"]
            if step.get("id") == step_id
        )

    def test_precheck_handles_automerge_label_and_ready_for_review_events(self):
        precheck = self.jobs["precheck"]
        condition = precheck["if"]

        self.assertIn("github.event.pull_request.state == 'open'", condition)
        self.assertIn("github.event.action == 'labeled'", condition)
        self.assertIn("github.event.action == 'unlabeled'", condition)
        self.assertIn("github.event.label.name == 'automerge'", condition)
        self.assertIn("github.event.action == 'ready_for_review'", condition)

    def test_caller_only_cancels_when_automerge_label_is_removed(self):
        cancel_condition = self.caller["concurrency"]["cancel-in-progress"]

        self.assertIn("github.event.action == 'unlabeled'", cancel_condition)
        self.assertIn("github.event.label.name == 'automerge'", cancel_condition)

    def test_caller_isolates_unrelated_label_events(self):
        group = self.caller["concurrency"]["group"]

        self.assertIn("github.event.label.name == 'automerge'", group)
        self.assertIn("github.event.action == 'ready_for_review'", group)
        self.assertIn(
            "format('pr-automerge-unrelated-{0}', github.run_id)",
            group,
        )
        self.assertIn(
            "format('pr-automerge-unrelated-{0}', github.run_id)",
            self.caller_template,
        )

    def test_origin_compares_head_and_target_repositories(self):
        origin = self.step("precheck", "origin")

        self.assertEqual(
            origin["env"]["HEAD_REPOSITORY"],
            "${{ github.event.pull_request.head.repo.full_name }}",
        )
        self.assertEqual(origin["env"]["REPOSITORY"], "${{ github.repository }}")
        self.assertIn('[ "$HEAD_REPOSITORY" = "$REPOSITORY" ]', origin["run"])
        self.assertIn("is-self=$IS_SELF", origin["run"])

    def test_precheck_removes_automerge_label_from_forks(self):
        removal = self.step("precheck", "remove-fork-label")

        self.assertIn(
            "steps.automerge-label.outputs.has-automerge == 'true'",
            removal["if"],
        )
        self.assertIn("steps.origin.outputs.is-self != 'true'", removal["if"])
        self.assertIn("--remove-label automerge", removal["run"])

    def test_precheck_selects_authorized_mode_and_native_operation(self):
        precheck = self.jobs["precheck"]
        decision = self.step("precheck", "decision")

        self.assertEqual(set(precheck["outputs"]), {"mode", "operation", "reason"})
        self.assertEqual(precheck["outputs"]["mode"], "${{ steps.decision.outputs.mode }}")
        self.assertEqual(
            precheck["outputs"]["operation"],
            "${{ steps.decision.outputs.operation }}",
        )
        self.assertEqual(
            precheck["outputs"]["reason"],
            "${{ steps.decision.outputs.reason }}",
        )
        self.assertIn(
            'REASON="Automerge label was removed because pull request head repository is a fork."',
            decision["run"],
        )
        self.assertIn('REASON="Automerge mode is disabled."', decision["run"])
        self.assertIn(
            'REASON="Pull request head repository is a fork."',
            decision["run"],
        )
        self.assertIn('REASON="PR is draft."', decision["run"])
        self.assertIn('REASON="Automerge label is missing."', decision["run"])
        self.assertIn('MODE="poll"', decision["run"])
        self.assertIn('MODE="native"', decision["run"])
        self.assertIn('OPERATION="enable"', decision["run"])
        self.assertIn('OPERATION="disable"', decision["run"])

    def test_merge_job_uses_precheck_outputs(self):
        merge = self.jobs["merge"]
        native_merge = self.step("merge", "native-merge")

        self.assertEqual(merge["needs"], "precheck")
        self.assertEqual(
            merge["if"],
            "${{ needs.precheck.result == 'success' }}",
        )
        self.assertEqual(
            native_merge["if"],
            "${{ needs.precheck.outputs.mode == 'native' }}",
        )
        self.assertEqual(
            native_merge["env"]["OPERATION"],
            "${{ needs.precheck.outputs.operation }}",
        )
        self.assertIn("--auto --squash", native_merge["run"])
        self.assertIn("--disable-auto", native_merge["run"])
        self.assertIn("merge-summary=Enabled auto-merge.", native_merge["run"])
        self.assertIn(
            "merge-summary=Disabled auto-merge after automerge label was removed.",
            native_merge["run"],
        )

    def test_poll_job_uses_precheck_mode(self):
        merge = self.jobs["merge"]
        checks = self.step("merge", "checks")

        self.assertEqual(
            checks["if"],
            "${{ needs.precheck.outputs.mode == 'poll' }}",
        )
        self.assertEqual(merge["needs"], "precheck")

    def test_poll_rechecks_label_before_merge(self):
        poll_merge = self.step("merge", "poll-merge")

        self.assertEqual(
            poll_merge["if"],
            "${{ needs.precheck.outputs.mode == 'poll' && steps.checks.outcome == 'success' }}",
        )
        self.assertNotIn("steps.current-label", poll_merge["if"])
        self.assertNotIn("steps.current-label", poll_merge["run"])
        self.assertIn("gh pr view", poll_merge["run"])
        self.assertIn('if [ "$HAS_AUTOMERGE" != "true" ]', poll_merge["run"])
        self.assertIn("merge-summary=Merged PR.", poll_merge["run"])

    def test_summary_runs_after_merge_steps(self):
        merge = self.jobs["merge"]
        summary_step = self.step("merge", "workflow-summary")

        self.assertEqual(summary_step["if"], "${{ always() }}")
        self.assertIn(
            "steps.native-merge.outcome",
            summary_step["env"]["AUTOMERGE_RESULT"],
        )
        self.assertIn(
            "steps.poll-merge.outcome",
            summary_step["env"]["AUTOMERGE_RESULT"],
        )
        self.assertIn(
            "steps.native-merge.outputs.merge-summary",
            summary_step["env"]["AUTOMERGE_SUMMARY"],
        )
        self.assertIn(
            "steps.poll-merge.outputs.merge-summary",
            summary_step["env"]["AUTOMERGE_SUMMARY"],
        )
        self.assertIn('elif [ -n "${PRECHECK_REASON}" ]', summary_step["run"])
        self.assertIn('echo "Skipped: ${PRECHECK_REASON}"', summary_step["run"])
        self.assertIn(
            'elif [ "${AUTOMERGE_RESULT}" = "failure" ]',
            summary_step["run"],
        )
        self.assertIn('elif [ -n "${AUTOMERGE_SUMMARY}" ]', summary_step["run"])
        self.assertIn('echo "${AUTOMERGE_SUMMARY}"', summary_step["run"])
        self.assertEqual(merge["needs"], "precheck")


if __name__ == "__main__":
    unittest.main()

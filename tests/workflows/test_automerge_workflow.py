from pathlib import Path
import unittest

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "automerge.yml"
CALLER_PATH = REPO_ROOT / ".github" / "workflows" / "pr_automerge.yml"
TEMPLATE_CALLER_PATH = (
    REPO_ROOT
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

    def test_precheck_handles_all_reconciliation_events(self):
        precheck = self.jobs["precheck"]
        condition = precheck["if"]

        self.assertIn("github.event.pull_request.state == 'open'", condition)
        self.assertIn("github.event.action == 'labeled'", condition)
        self.assertIn("github.event.action == 'unlabeled'", condition)
        self.assertIn("github.event.action == 'ready_for_review'", condition)

    def test_caller_queues_label_events_without_cancelling_required_checks(self):
        concurrency = self.caller["concurrency"]

        self.assertEqual(
            concurrency["group"],
            "pr-automerge-${{ github.event.pull_request.number || github.ref }}",
        )
        self.assertIs(False, concurrency["cancel-in-progress"])
        self.assertIn(
            "group: \"pr-automerge-${{ github.event.pull_request.number || github.ref }}\"",
            self.caller_template,
        )
        self.assertIn("cancel-in-progress: false", self.caller_template)

    def test_origin_compares_head_and_target_repositories(self):
        origin = self.step("precheck", "origin")

        self.assertEqual(
            origin["env"]["HAS_AUTOMERGE_LABEL"],
            "${{ steps.automerge-label.outputs.has-automerge-label }}",
        )
        self.assertEqual(
            origin["env"]["HEAD_REPOSITORY"],
            "${{ github.event.pull_request.head.repo.full_name }}",
        )
        self.assertEqual(origin["env"]["GH_TOKEN"], "${{ secrets.token }}")
        self.assertEqual(origin["env"]["REPOSITORY"], "${{ github.repository }}")
        self.assertIn('[ "$HEAD_REPOSITORY" = "$REPOSITORY" ]', origin["run"])
        self.assertIn("is-self=$IS_SELF", origin["run"])
        self.assertIn("automerge-label-removed=$AUTOMERGE_LABEL_REMOVED", origin["run"])

    def test_origin_removes_automerge_label_from_forks(self):
        origin = self.step("precheck", "origin")

        self.assertIn('if [ "$HAS_AUTOMERGE_LABEL" = "true" ]', origin["run"])
        self.assertIn(
            '&& [ "$IS_SELF" != "true" ]; then',
            origin["run"],
        )
        self.assertIn("--remove-label automerge", origin["run"])

    def test_precheck_selects_authorized_mode(self):
        precheck = self.jobs["precheck"]
        decision = self.step("precheck", "decision")

        self.assertEqual(set(precheck["outputs"]), {"mode", "reason"})
        self.assertEqual(precheck["outputs"]["mode"], "${{ steps.decision.outputs.mode }}")
        self.assertEqual(
            precheck["outputs"]["reason"],
            "${{ steps.decision.outputs.reason }}",
        )
        self.assertIn(
            'REASON="Automerge label was removed because pull request head repository is a fork."',
            decision["run"],
        )
        self.assertIn("AUTOMERGE_LABEL_REMOVED", decision["run"])
        self.assertIn('REASON="Automerge mode is disabled."', decision["run"])
        self.assertIn(
            'REASON="Pull request head repository is a fork."',
            decision["run"],
        )
        self.assertIn('REASON="PR is draft."', decision["run"])
        self.assertIn('REASON="Automerge state is not active."', decision["run"])
        self.assertIn('MODE="poll"', decision["run"])
        self.assertIn('MODE="native"', decision["run"])
        self.assertNotIn("OPERATION", decision["run"])

    def test_merge_job_uses_precheck_outputs(self):
        merge = self.jobs["merge"]
        native_merge = self.step("merge", "native-merge")

        self.assertEqual(merge["needs"], "precheck")
        self.assertEqual(
            merge["if"],
            "${{ needs.precheck.result == 'success' && needs.precheck.outputs.mode != '' }}",
        )
        self.assertEqual(
            native_merge["if"],
            "${{ needs.precheck.outputs.mode == 'native' }}",
        )
        self.assertIn("--auto --squash", native_merge["run"])
        self.assertNotIn("--disable-auto", native_merge["run"])
        self.assertIn("--json state", native_merge["run"])
        self.assertIn('if [ "$PR_STATE" != "OPEN" ]', native_merge["run"])
        self.assertIn("merge-summary=Enabled auto-merge.", native_merge["run"])

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
        self.assertIn("--json state,labels", poll_merge["run"])
        self.assertIn('if [ "$PR_STATE" != "OPEN" ]', poll_merge["run"])
        self.assertIn('if [ "$HAS_AUTOMERGE_LABEL" != "true" ]', poll_merge["run"])
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

from pathlib import Path
import unittest

import yaml


WORKFLOW_PATH = Path(__file__).resolve().parents[2] / "workflows" / "automerge.yml"
CALLER_PATH = Path(__file__).resolve().parents[2] / "workflows" / "pr_automerge.yml"


class AutomergeWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
        cls.jobs = workflow["jobs"]
        cls.caller = yaml.safe_load(CALLER_PATH.read_text(encoding="utf-8"))

    def step(self, job_id, step_id):
        return next(
            step
            for step in self.jobs[job_id]["steps"]
            if step.get("id") == step_id
        )

    def test_prepare_handles_automerge_label_and_ready_for_review_events(self):
        condition = self.jobs["prepare"]["if"]

        self.assertIn("github.event.pull_request.state == 'open'", condition)
        self.assertIn("github.event.action == 'labeled'", condition)
        self.assertIn("github.event.action == 'unlabeled'", condition)
        self.assertIn("github.event.label.name == 'automerge'", condition)
        self.assertIn("github.event.action == 'ready_for_review'", condition)

    def test_caller_only_cancels_when_automerge_label_is_removed(self):
        cancel_condition = self.caller["concurrency"]["cancel-in-progress"]

        self.assertIn("github.event.action == 'unlabeled'", cancel_condition)
        self.assertIn("github.event.label.name == 'automerge'", cancel_condition)

    def test_origin_compares_head_and_target_repositories(self):
        origin = self.step("prepare", "origin")

        self.assertEqual(
            origin["env"]["HEAD_REPOSITORY"],
            "${{ github.event.pull_request.head.repo.full_name }}",
        )
        self.assertEqual(origin["env"]["REPOSITORY"], "${{ github.repository }}")
        self.assertIn('[ "$HEAD_REPOSITORY" = "$REPOSITORY" ]', origin["run"])
        self.assertIn("is-self=$IS_SELF", origin["run"])

    def test_prepare_removes_automerge_label_from_forks(self):
        removal = self.step("prepare", "remove-fork-label")

        self.assertIn(
            "steps.automerge-label.outputs.has-automerge == 'true'",
            removal["if"],
        )
        self.assertIn("steps.origin.outputs.is-self != 'true'", removal["if"])
        self.assertIn("--remove-label automerge", removal["run"])

    def test_prepare_selects_authorized_mode_and_native_operation(self):
        prepare = self.jobs["prepare"]
        decision = self.step("prepare", "decision")

        self.assertEqual(set(prepare["outputs"]), {"mode", "operation", "reason"})
        self.assertEqual(prepare["outputs"]["mode"], "${{ steps.decision.outputs.mode }}")
        self.assertEqual(
            prepare["outputs"]["operation"],
            "${{ steps.decision.outputs.operation }}",
        )
        self.assertEqual(
            prepare["outputs"]["reason"],
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

    def test_native_job_uses_prepared_mode_and_operation(self):
        native = self.jobs["native"]
        native_merge = self.step("native", "native-merge")

        self.assertEqual(native["needs"], "prepare")
        self.assertEqual(
            native["if"],
            "${{ needs.prepare.result == 'success' && needs.prepare.outputs.mode == 'native' }}",
        )
        self.assertEqual(
            native_merge["env"]["OPERATION"],
            "${{ needs.prepare.outputs.operation }}",
        )
        self.assertIn("--auto --squash", native_merge["run"])
        self.assertIn("--disable-auto", native_merge["run"])
        self.assertEqual(
            native["outputs"]["merge-summary"],
            "${{ steps.native-merge.outputs.merge-summary }}",
        )
        self.assertIn("merge-summary=Enabled auto-merge.", native_merge["run"])
        self.assertIn(
            "merge-summary=Disabled auto-merge after automerge label was removed.",
            native_merge["run"],
        )

    def test_poll_job_uses_prepared_mode(self):
        poll = self.jobs["poll"]

        self.assertEqual(poll["needs"], "prepare")
        self.assertEqual(
            poll["if"],
            "${{ needs.prepare.result == 'success' && needs.prepare.outputs.mode == 'poll' }}",
        )

    def test_poll_rechecks_label_before_merge(self):
        current_label = self.step("poll", "current-label")
        poll_merge = self.step("poll", "poll-merge")

        self.assertIn("gh pr view", current_label["run"])
        self.assertIn("steps.checks.outcome == 'success'", current_label["if"])
        self.assertIn(
            "steps.current-label.outputs.has-automerge == 'true'",
            poll_merge["if"],
        )
        self.assertEqual(
            self.jobs["poll"]["outputs"]["merge-summary"],
            "${{ steps.poll-merge.outputs.merge-summary }}",
        )
        self.assertIn("merge-summary=Merged PR.", poll_merge["run"])

    def test_summary_runs_after_all_behavior_jobs(self):
        summary = self.jobs["summary"]

        self.assertEqual(summary["needs"], ["prepare", "native", "poll"])
        self.assertIn("always()", summary["if"])
        self.assertIn("needs.prepare.result != 'skipped'", summary["if"])
        summary_step = summary["steps"][0]
        self.assertIn(
            "needs.native.result",
            summary_step["env"]["AUTOMERGE_RESULT"],
        )
        self.assertIn(
            "needs.poll.result",
            summary_step["env"]["AUTOMERGE_RESULT"],
        )
        self.assertIn(
            "needs.native.outputs.merge-summary",
            summary_step["env"]["AUTOMERGE_SUMMARY"],
        )
        self.assertIn(
            "needs.poll.outputs.merge-summary",
            summary_step["env"]["AUTOMERGE_SUMMARY"],
        )
        self.assertIn('elif [ -n "${PREPARE_REASON}" ]', summary_step["run"])
        self.assertIn('echo "Skipped: ${PREPARE_REASON}"', summary_step["run"])
        self.assertIn(
            'elif [ "${AUTOMERGE_RESULT}" = "failure" ]',
            summary_step["run"],
        )
        self.assertIn('elif [ -n "${AUTOMERGE_SUMMARY}" ]', summary_step["run"])
        self.assertIn('echo "${AUTOMERGE_SUMMARY}"', summary_step["run"])


if __name__ == "__main__":
    unittest.main()

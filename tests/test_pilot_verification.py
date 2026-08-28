import unittest

from nfl_fidos.pilot_verification import summarize_pilot_feedback


class PilotVerificationTests(unittest.TestCase):
    def test_summary_reports_role_coverage_metrics_without_auto_approval(self):
        feedback = [
            {"organization_id":"ORG-PILOT", "session_id":"UX-SESSION-1", "task_id":"TASK-1", "user_role":"program_owner", "outcome":"completed", "severity":"note", "duration_seconds":30, "satisfaction_score":5, "accessibility_issue":False},
            {"organization_id":"ORG-PILOT", "session_id":"UX-SESSION-2", "task_id":"TASK-1", "user_role":"coach_staff", "outcome":"completed", "severity":"minor", "duration_seconds":45, "satisfaction_score":4, "accessibility_issue":False},
            {"organization_id":"ORG-PILOT", "session_id":"UX-SESSION-3", "task_id":"TASK-1", "user_role":"analyst", "outcome":"partially_completed", "severity":"minor", "duration_seconds":60, "satisfaction_score":3, "accessibility_issue":True},
            {"organization_id":"ORG-PILOT", "session_id":"UX-SESSION-4", "task_id":"TASK-1", "user_role":"player", "outcome":"completed", "severity":"note", "duration_seconds":35, "satisfaction_score":4, "accessibility_issue":False},
        ]
        summary = summarize_pilot_feedback(organization_id="ORG-PILOT", feedback=feedback)
        self.assertEqual(summary["status"], "ready_for_moderator_review")
        self.assertEqual(summary["missing_pilot_roles"], [])
        self.assertEqual(summary["feedback_count"], 4)
        self.assertEqual(summary["accessibility_issue_count"], 1)
        self.assertFalse(summary["pilot_validation_complete"])

    def test_summary_is_tenant_scoped_and_blocks_without_evidence(self):
        summary = summarize_pilot_feedback(organization_id="ORG-PILOT", feedback=[{"organization_id":"ORG-OTHER", "user_role":"player"}])
        self.assertEqual(summary["status"], "blocked")
        self.assertEqual(summary["feedback_count"], 0)
        self.assertIn("feedback is required", summary["blockers"])


if __name__ == "__main__":
    unittest.main()

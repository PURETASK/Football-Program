import unittest

from nfl_fidos.usability_feedback import build_usability_feedback, validate_usability_feedback


class UsabilityFeedbackTests(unittest.TestCase):
    def _feedback(self):
        return build_usability_feedback(
            feedback_id="UX-FEEDBACK-001",
            organization_id="ORG-1",
            session_id="UX-SESSION-001",
            user_role="coach_staff",
            screen_id="SCREEN-GOVERNANCE",
            task_id="TASK-LOAD-GATE",
            outcome="completed",
            severity="note",
            feedback_text="The approval state was understandable.",
            submitted_at="2026-08-23T12:00:00Z",
            evidence_refs=["BROWSER-VALIDATION-LOCAL-001"],
        )

    def test_role_scoped_feedback_validates_and_preserves_review_boundary(self):
        feedback = self._feedback()
        result = validate_usability_feedback(feedback, screen_ids={"SCREEN-GOVERNANCE"})
        self.assertEqual(result["status"], "valid")
        self.assertFalse(result["human_review_required"])
        self.assertEqual(feedback["disposition"], "new")

    def test_blocked_accessibility_feedback_requires_review(self):
        feedback = self._feedback()
        feedback["outcome"] = "blocked"
        feedback["accessibility_issue"] = True
        result = validate_usability_feedback(feedback, screen_ids={"SCREEN-GOVERNANCE"})
        self.assertEqual(result["status"], "valid")
        self.assertTrue(result["human_review_required"])

    def test_unknown_screen_and_missing_evidence_are_rejected(self):
        feedback = self._feedback()
        feedback["screen_id"] = "SCREEN-MISSING"
        feedback["evidence_refs"] = []
        result = validate_usability_feedback(feedback, screen_ids={"SCREEN-GOVERNANCE"})
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any(issue["code"] == "UX-FEEDBACK-SCREEN" for issue in result["issues"]))
        self.assertTrue(any(issue["code"] == "UX-FEEDBACK-EVIDENCE" for issue in result["issues"]))


if __name__ == "__main__":
    unittest.main()

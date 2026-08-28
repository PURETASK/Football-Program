import tempfile
import unittest
from pathlib import Path

from nfl_fidos.operator_summary import build_operator_summary
from nfl_fidos.repository import JsonRepository
from nfl_fidos.tenant_repository import TenantRepository


class OperatorSummaryTests(unittest.TestCase):
    def test_summary_is_scoped_and_role_sections_are_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-SUMMARY", actor="COACH")
            repository.put("media_processing_jobs", "MEDIA-JOB-SUMMARY", {"id":"MEDIA-JOB-SUMMARY", "organization_id":"ORG-SUMMARY", "status":"retryable"}, reason="fixture")
            result = build_operator_summary(repository=repository, role="coach_staff", stage="STAGE-0", work_package="STAGE-0A", eval_result={"status":"passed", "passed":66, "failed":0})
            self.assertEqual(result["organization_id"], "ORG-SUMMARY")
            self.assertIn("game_plan", result["allowed_sections"])
            self.assertNotIn("governance", result["allowed_sections"])
            self.assertEqual(result["media_job_counts"]["retryable"], 1)
            self.assertEqual(result["pending_review_count"], 1)
            self.assertIsNone(result["organization_population"])

    def test_owner_summary_surfaces_population_blockers_without_activating(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-SUMMARY", actor="OWNER")
            result = build_operator_summary(repository=repository, role="program_owner", stage="STAGE-0", work_package="STAGE-0A", season="2026", eval_result={"status":"passed", "passed":66, "failed":0})
            self.assertEqual(result["organization_population"]["status"], "population_incomplete")
            self.assertEqual(result["organization_population"]["required_component_count"], 13)
            self.assertFalse(result["organization_population"]["activation_performed"])


if __name__ == "__main__":
    unittest.main()

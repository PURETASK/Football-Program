import tempfile
import unittest
from pathlib import Path

from nfl_fidos.repository import JsonRepository
from nfl_fidos.media_jobs import MediaProcessingJobService
from nfl_fidos.scheduled_operations import ScheduledOperationsService
from nfl_fidos.tenant_repository import TenantRepository


class ScheduledOperationsTests(unittest.TestCase):
    def test_plan_is_dry_run_and_bounds_all_operation_families(self):
        with tempfile.TemporaryDirectory() as directory:
            tenant = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-SCHEDULE", actor="OWNER")
            MediaProcessingJobService(tenant).create_job(job_id="MEDIA-JOB-SCHEDULE-INDEX", asset_id="FILM-SCHEDULE-INDEX", operation="index", payload={"file_path":str(Path(directory) / "game.mp4"), "allowed_roots":[directory]}, requested_by="OWNER")
            service = ScheduledOperationsService(tenant, environment="validation")
            plan = service.run(actor="OWNER", worker_id="WORKER", execute=False, max_sources=2, max_transforms=3, retention_days=30)
            self.assertTrue(plan["dry_run"])
            self.assertEqual(plan["max_sources"], 2)
            self.assertEqual(plan["max_transforms"], 3)
            self.assertEqual(plan["queued_transform_count"], 1)
            self.assertFalse(plan["destructive_action_required"])

    def test_production_execution_is_blocked_by_stage_gate(self):
        with tempfile.TemporaryDirectory() as directory:
            tenant = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-SCHEDULE", actor="OWNER")
            result = ScheduledOperationsService(tenant, environment="production", control_root=Path(__file__).parents[1]).run(actor="OWNER", worker_id="WORKER", execute=True)
            self.assertEqual(result["status"], "blocked")
            self.assertIn("Stage 0", result["blocker"])


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path

from nfl_fidos.project_audit import run_project_audit


class ProjectAuditTests(unittest.TestCase):
    def test_checkpoint_passes_without_claiming_completion(self):
        root = Path(__file__).resolve().parents[1]
        result = run_project_audit(root=root, run_evals=False)
        self.assertEqual(result["status"], "foundation_verified")
        self.assertTrue(all(result["checks"].values()))
        self.assertFalse(result["completion_claimed"])
        self.assertGreater(result["remaining_stage_count"], 0)
        self.assertFalse(result["control"]["production_implementation_allowed"])


if __name__ == "__main__":
    unittest.main()

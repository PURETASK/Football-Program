import unittest
from pathlib import Path

from nfl_fidos.play_designer_quality import run_export_matrix_rehearsal, run_large_play_rehearsal, run_play_designer_quality_gates


class PlayDesignerQualityTests(unittest.TestCase):
    def test_large_play_rehearsal_measures_validation_budget(self):
        result = run_large_play_rehearsal(element_count=120, max_duration_ms=2000)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["element_count"], 120)
        self.assertLessEqual(result["duration_ms"], result["budget_ms"])

    def test_quality_gates_cover_accessibility_offline_print_performance_and_visuals(self):
        result = run_play_designer_quality_gates(root=Path(__file__).parents[1], element_count=80)
        self.assertEqual(result["status"], "passed")
        check_ids = {check["id"] for check in result["checks"]}
        self.assertEqual(check_ids, {"PDQ-ACCESSIBILITY", "PDQ-KEYBOARD-AUTHORING", "PDQ-OFFLINE-ENCRYPTION", "PDQ-PRINT-ACCESSIBILITY", "PDQ-LARGE-PLAY-PERFORMANCE", "PDQ-COLLAB-CONVERGENCE-REHEARSAL", "PDQ-EXPORT-MATRIX-REHEARSAL", "PDQ-RULE-PROFILE-CATALOG", "PDQ-VISUAL-REGRESSION"})
        self.assertFalse(result["external_state_changed"])

    def test_export_matrix_rehearses_all_local_output_families(self):
        result = run_export_matrix_rehearsal()
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["case_count"], 14)
        self.assertEqual(result["passed_count"], 14)
        self.assertTrue(all(item["integrity"] == "verified" for item in result["results"]))
        self.assertFalse(result["external_state_changed"])


if __name__ == "__main__":
    unittest.main()

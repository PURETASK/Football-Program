import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos import run_minimum_eval_suite


class EvaluationSuiteTests(unittest.TestCase):
    def test_minimum_eval_suite_passes_all_named_families(self):
        result = run_minimum_eval_suite()
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["failed"], 0)
        self.assertEqual(result["passed"], 97)
        self.assertEqual(len(result["coverage"]), 97)

    def test_eval_results_are_machine_readable(self):
        result = run_minimum_eval_suite(suite_id="EVAL-SUITE-TEST")
        self.assertEqual(result["suite_id"], "EVAL-SUITE-TEST")
        self.assertTrue(all("family_id" in family and "checks" in family for family in result["families"]))


if __name__ == "__main__":
    unittest.main()

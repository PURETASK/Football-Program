import copy
import json
import unittest
from pathlib import Path

from nfl_fidos.evaluation_scenarios import validate_evaluation_scenario_corpus


class EvaluationScenarioCorpusTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / "governance" / "evaluation-scenario-corpus.json"
        self.corpus = json.loads(path.read_text(encoding="utf-8"))

    def test_scenario_corpus_covers_all_governance_domains(self):
        result = validate_evaluation_scenario_corpus(self.corpus)
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["scenario_count"], 48)
        self.assertEqual(result["domain_count"], 12)

    def test_unsupported_domain_and_unreviewed_nuance_are_rejected(self):
        invalid = copy.deepcopy(self.corpus)
        invalid["scenarios"][0]["domain"] = "uncontrolled_domain"
        invalid["scenarios"][1]["expected_outcome"] = "review_required"
        invalid["scenarios"][1]["human_review_required"] = False
        result = validate_evaluation_scenario_corpus(invalid)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("unsupported domain" in error for error in result["errors"]))
        self.assertTrue(any("requires human review" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()

import json
import unittest
from pathlib import Path

from nfl_fidos.mvp_strategy import evaluate_mvp_wave, validate_mvp_strategy


class MVPStrategyTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / "delivery" / "mvp-strategy.json"
        self.strategy = json.loads(path.read_text(encoding="utf-8"))

    def test_strategy_has_sequential_vertical_slices(self):
        result = validate_mvp_strategy(self.strategy)
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["wave_count"], 3)

    def test_wave_blocks_without_acceptance_and_approval(self):
        result = evaluate_mvp_wave(wave=self.strategy["waves"][0], completed_capabilities=set(self.strategy["waves"][0]["capabilities"]), eval_result={"status":"passed"}, acceptance_evidence=[], feature_flags={"production_recommendations":False}, approval=None)
        self.assertEqual(result["status"], "blocked")

    def test_wave_is_ready_with_complete_evidence_and_flags_off(self):
        wave = self.strategy["waves"][0]
        result = evaluate_mvp_wave(wave=wave, completed_capabilities=set(wave["capabilities"]), eval_result={"status":"passed"}, acceptance_evidence=["TEST-1","AUDIT-1"], feature_flags={"production_recommendations":False}, approval="OWNER-APPROVAL-1")
        self.assertEqual(result["status"], "ready")

    def test_unknown_wave_dependency_is_rejected(self):
        strategy = json.loads(json.dumps(self.strategy))
        strategy["waves"][1]["dependencies"].append("WAVE-999")
        self.assertEqual(validate_mvp_strategy(strategy)["status"], "invalid")

import tempfile
import unittest
from pathlib import Path

from nfl_fidos.monitoring_contract import load_monitoring_contract
from nfl_fidos.monitoring_registration import validate_monitoring_registration


class MonitoringRegistrationTests(unittest.TestCase):
    def test_validation_registration_is_ready_without_external_write(self):
        with tempfile.TemporaryDirectory() as directory:
            result = validate_monitoring_registration(contract=load_monitoring_contract(), environ={"NFL_FIDOS_MONITORING_BACKEND":"structured_jsonl", "NFL_FIDOS_MONITORING_REGISTRATION_REF":"MONITORING-REG-001", "NFL_FIDOS_OBSERVABILITY_PATH":str(Path(directory) / "events.jsonl")}, environment="validation")
            self.assertEqual(result["status"], "ready")
            self.assertFalse(result["external_registration_performed"])
            self.assertFalse(result["external_state_changed"])

    def test_production_registration_and_sink_parent_are_fail_closed(self):
        result = validate_monitoring_registration(contract=load_monitoring_contract(), environ={"NFL_FIDOS_MONITORING_BACKEND":"vendor_unknown", "NFL_FIDOS_OBSERVABILITY_PATH":"C:\\missing\\events.jsonl"}, environment="production")
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("structured_jsonl" in issue for issue in result["issues"]))
        self.assertTrue(any("MONITORING-REG" in issue for issue in result["issues"]))


if __name__ == "__main__":
    unittest.main()

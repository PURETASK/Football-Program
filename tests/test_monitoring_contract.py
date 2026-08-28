import unittest

from nfl_fidos.monitoring_contract import load_monitoring_contract, validate_monitoring_contract


class MonitoringContractTests(unittest.TestCase):
    def test_monitoring_contract_is_provider_neutral_and_complete(self):
        contract = load_monitoring_contract()
        result = validate_monitoring_contract(contract)
        self.assertEqual(result["status"], "valid")
        self.assertTrue(result["provider_neutral"])
        self.assertEqual(result["alert_count"], 4)

    def test_missing_backup_alert_is_rejected(self):
        contract = load_monitoring_contract()
        contract["alerts"] = [alert for alert in contract["alerts"] if alert["id"] != "ALERT-BACKUP-MISMATCH"]
        self.assertEqual(validate_monitoring_contract(contract)["status"], "invalid")


if __name__ == "__main__":
    unittest.main()

import unittest
from pathlib import Path

from nfl_fidos.security_audit import run_security_audit


class SecurityAuditTests(unittest.TestCase):
    def test_local_security_posture_has_required_control_families(self):
        root = Path(__file__).parents[1]
        report = run_security_audit(root=root, environ={"NFL_FIDOS_RATE_LIMIT_PER_MINUTE": "120"}, environment="validation")
        self.assertEqual(report["status"], "ready")
        self.assertFalse(report["production_implementation_allowed"])
        self.assertTrue({"tenant_isolation", "signed_exports", "encrypted_offline_storage", "redacted_audit", "recovery"}.issubset(report["control_families"]))

    def test_invalid_rate_limit_is_a_blocker(self):
        report = run_security_audit(root=Path(__file__).parents[1], environ={"NFL_FIDOS_RATE_LIMIT_PER_MINUTE": "0"}, environment="validation")
        self.assertEqual(report["status"], "blocked")
        self.assertTrue(any(check["id"] == "SEC-RATE-LIMIT" and check["status"] == "blocker" for check in report["checks"]))


if __name__ == "__main__":
    unittest.main()

import json
import unittest
from pathlib import Path

from nfl_fidos.pilot_readiness import evaluate_pilot_readiness


class PilotReadinessTests(unittest.TestCase):
    def setUp(self):
        strategy = json.loads((Path(__file__).resolve().parents[1] / "delivery" / "mvp-strategy.json").read_text(encoding="utf-8"))
        self.wave = strategy["waves"][0]

    def test_pilot_is_blocked_without_roles_rollback_and_approval(self):
        result = evaluate_pilot_readiness(organization_id="ORG-PILOT", pilot_users=[], wave=self.wave, completed_capabilities=set(self.wave["capabilities"]), eval_result={"status":"passed"}, acceptance_evidence=["TEST-1"], feature_flags={"production_recommendations":False}, rollback_tested=False, owner_approval=None)
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("role coverage" in blocker for blocker in result["blockers"]))
        self.assertTrue(any("rollback" in blocker for blocker in result["blockers"]))

    def test_pilot_becomes_ready_only_with_complete_evidence_and_approval(self):
        users = [{"id":"OWNER", "role":"program_owner"}, {"id":"COACH", "role":"coach_staff"}, {"id":"ANALYST", "role":"analyst"}, {"id":"PLAYER", "role":"player"}]
        result = evaluate_pilot_readiness(organization_id="ORG-PILOT", pilot_users=users, wave=self.wave, completed_capabilities=set(self.wave["capabilities"]), eval_result={"status":"passed"}, acceptance_evidence=["TEST-1","AUDIT-1"], feature_flags={"production_recommendations":False}, rollback_tested=True, owner_approval="APPROVAL-1")
        self.assertEqual(result["status"], "ready_for_pilot")
        self.assertFalse(result["production_implementation_allowed"])


if __name__ == "__main__":
    unittest.main()

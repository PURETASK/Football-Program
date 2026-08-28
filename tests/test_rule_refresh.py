import copy
import json
import unittest
from pathlib import Path

from nfl_fidos.rule_refresh import approve_rule_source_refresh, plan_rule_source_refresh


class RuleRefreshTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).parents[1]
        self.current = json.loads((root / "rules" / "authoritative-source-registry.json").read_text(encoding="utf-8"))

    def test_candidate_change_requires_jurisdiction_review_and_cannot_promote_automatically(self):
        candidate = copy.deepcopy(self.current)
        candidate["registry_id"] = "NFL-RULE-SOURCES-CANDIDATE-2027"
        candidate["sources"][0]["version"] = "2027"
        candidate["sources"][0]["effective_date"] = "2027-01-01"
        candidate["sources"][0]["status"] = "proposed"
        plan = plan_rule_source_refresh(current_registry=self.current, candidate_registry=candidate, review_id="RULE-REFRESH-001")
        self.assertEqual(plan["status"], "under_review")
        self.assertEqual(plan["changes"][0]["change"], "updated")
        self.assertTrue(plan["human_review_required"])
        self.assertFalse(plan["promotion_allowed"])

    def test_refresh_approval_requires_owner_decision_and_still_does_not_activate_production(self):
        candidate = copy.deepcopy(self.current)
        candidate["registry_id"] = "NFL-RULE-SOURCES-CANDIDATE-2027"
        candidate["sources"][0]["version"] = "2027"
        candidate["sources"][0]["status"] = "proposed"
        plan = plan_rule_source_refresh(current_registry=self.current, candidate_registry=candidate, review_id="RULE-REFRESH-002")
        rejected = approve_rule_source_refresh(plan, approver_role="analyst", decision_ref="DEC-RULE-002", candidate_registry=candidate)
        self.assertEqual(rejected["status"], "rejected")
        approved = approve_rule_source_refresh(plan, approver_role="program_owner", decision_ref="DEC-RULE-002", candidate_registry=candidate)
        self.assertEqual(approved["status"], "approved")
        self.assertFalse(approved["promotion_allowed"])
        self.assertTrue(approved["human_review_required"])
        self.assertEqual(approved["promoted_registry"]["status"], "current")


if __name__ == "__main__":
    unittest.main()

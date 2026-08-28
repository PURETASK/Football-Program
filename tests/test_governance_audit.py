import json
import unittest
from pathlib import Path

from nfl_fidos.governance_audit import run_governance_audit, validate_eval_bible


class GovernanceAuditTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / "governance" / "eval-bible.json"
        self.bible = json.loads(path.read_text(encoding="utf-8"))

    def test_eval_bible_covers_high_risk_domains(self):
        result = validate_eval_bible(self.bible)
        self.assertEqual(result["status"], "valid")
        self.assertGreaterEqual(result["domain_count"], 12)

    def test_failed_suite_blocks_promotion(self):
        result = run_governance_audit(audit_id="AUDIT-001", eval_result={"status":"failed"}, critical_failures=[], safety_failures=[], permission_failures=[], audit_event_id="EVENT-1", observability_evidence=["TRACE-1"], human_approval="APPROVAL-1")
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(result["promotion_blocked"])

    def test_complete_governance_evidence_allows_promotion(self):
        result = run_governance_audit(audit_id="AUDIT-002", eval_result={"status":"passed"}, critical_failures=[], safety_failures=[], permission_failures=[], audit_event_id="EVENT-2", observability_evidence=["TRACE-2"], human_approval="APPROVAL-2")
        self.assertEqual(result["status"], "eligible_for_promotion")
        self.assertFalse(result["promotion_blocked"])

    def test_missing_human_approval_blocks(self):
        result = run_governance_audit(audit_id="AUDIT-003", eval_result={"status":"passed"}, critical_failures=[], safety_failures=[], permission_failures=[], audit_event_id="EVENT-3", observability_evidence=["TRACE-3"], human_approval=None)
        self.assertEqual(result["status"], "blocked")

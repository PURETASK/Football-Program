import unittest
from pathlib import Path


class AuditMasterPlanCliTests(unittest.TestCase):
    def test_cli_defaults_to_checked_in_plan_copy(self):
        from scripts import audit_master_plan

        root = Path(__file__).resolve().parents[1]
        self.assertEqual(audit_master_plan.DEFAULT_MARKDOWN, root / "governance" / "master-plan" / "NFL_Football_Intelligence_OS_Master_Codex_Plan_v1.0.md")
        self.assertEqual(audit_master_plan.DEFAULT_DOCX, root / "governance" / "master-plan" / "NFL_Football_Intelligence_OS_Master_Codex_Plan_v1.0.docx")
        self.assertTrue(audit_master_plan.DEFAULT_MARKDOWN.is_file())
        self.assertTrue(audit_master_plan.DEFAULT_DOCX.is_file())


if __name__ == "__main__":
    unittest.main()

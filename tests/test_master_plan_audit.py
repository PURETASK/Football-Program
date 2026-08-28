import json
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.master_plan_audit import audit_master_plan, parse_markdown_plan


class MasterPlanAuditTests(unittest.TestCase):
    def test_parser_extracts_all_roadmap_stages_and_deliverables(self):
        source = Path(r"C:\Users\onlyw\Downloads\NFL_Football_Intelligence_OS_Master_Codex_Plan_v1.0 (1).md")
        if not source.exists():
            self.skipTest("uploaded Master Plan is not mounted in this environment")
        parsed = parse_markdown_plan(source)
        self.assertEqual(len(parsed["stages"]), 26)
        self.assertEqual(parsed["stages"][0]["stage"], "STAGE-0")
        self.assertGreaterEqual(len(parsed["stages"][0]["required_deliverables"]), 1)

    def test_repository_conformance_passes_against_both_source_artifacts(self):
        root = Path(__file__).parents[1]
        markdown = Path(r"C:\Users\onlyw\Downloads\NFL_Football_Intelligence_OS_Master_Codex_Plan_v1.0 (1).md")
        docx = Path(r"C:\Users\onlyw\Downloads\NFL_Football_Intelligence_OS_Master_Codex_Plan_v1.0 (1).docx")
        if not markdown.exists() or not docx.exists():
            self.skipTest("uploaded Master Plan artifacts are not mounted in this environment")
        result = audit_master_plan(
            markdown,
            docx,
            root,
            root / "control" / "requirements-traceability.json",
        )
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["stage_count"], 26)
        self.assertEqual(result["traceability_stage_count"], 26)

    def test_missing_evidence_fails_without_mutating_ledger(self):
        root = Path(__file__).parents[1]
        markdown = Path(r"C:\Users\onlyw\Downloads\NFL_Football_Intelligence_OS_Master_Codex_Plan_v1.0 (1).md")
        docx = Path(r"C:\Users\onlyw\Downloads\NFL_Football_Intelligence_OS_Master_Codex_Plan_v1.0 (1).docx")
        if not markdown.exists() or not docx.exists():
            self.skipTest("uploaded Master Plan artifacts are not mounted in this environment")
        with tempfile.TemporaryDirectory() as directory:
            ledger = json.loads((root / "control" / "requirements-traceability.json").read_text(encoding="utf-8"))
            ledger["stages"][0]["evidence"].append("missing/not-real.json")
            ledger_path = Path(directory) / "ledger.json"
            ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
            result = audit_master_plan(
                markdown,
                docx,
                root,
                ledger_path,
            )
            self.assertEqual(result["status"], "failed")
            self.assertIn("STAGE-0", result["unreachable_evidence"])


if __name__ == "__main__":
    unittest.main()

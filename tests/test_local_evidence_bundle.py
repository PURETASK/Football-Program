import unittest
from pathlib import Path

from scripts.build_local_evidence_bundle import build_bundle


class LocalEvidenceBundleTests(unittest.TestCase):
    def test_bundle_composes_verified_non_activating_evidence(self):
        root = Path(__file__).resolve().parents[1]
        bundle = build_bundle(root=root, run_evals=False)
        self.assertEqual(bundle["status"], "valid")
        self.assertTrue(all(bundle["checks"].values()))
        self.assertFalse(bundle["safety"]["external_state_changed"])
        self.assertFalse(bundle["safety"]["production_implementation_allowed"])
        self.assertFalse(bundle["project_audit"]["completion_claimed"])
        self.assertEqual(bundle["stage0_owner_packet"]["review_status"], "ready_for_owner_review")
        self.assertFalse(bundle["stage0_owner_packet"]["safety"]["approval_recorded"])


if __name__ == "__main__":
    unittest.main()

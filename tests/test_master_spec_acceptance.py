import copy
import unittest

from nfl_fidos.master_spec_acceptance import build_stage25_spec_acceptance, load_master_spec, validate_stage25_spec_acceptance


class MasterSpecAcceptanceTests(unittest.TestCase):
    def test_valid_spec_can_produce_non_activating_acceptance_evidence(self):
        spec = load_master_spec()
        record = build_stage25_spec_acceptance(
            acceptance_id="ACCEPTANCE-STAGE25-001",
            spec=spec,
            approver="OWNER-1",
            rationale="Reviewed the compiled specification and linked audit evidence.",
            evidence_refs=["control/master-codex-build-spec.json", "control/requirements-traceability.json"],
            accepted_at="2026-08-23T12:00:00Z",
        )
        validation = validate_stage25_spec_acceptance(record, spec=spec)
        self.assertEqual(record["decision"], "accepted")
        self.assertEqual(validation["status"], "valid")
        self.assertFalse(record["production_implementation_allowed"])
        self.assertFalse(record["stage_advance_authorized"])

    def test_invalid_spec_cannot_be_accepted(self):
        spec = load_master_spec()
        spec["stage_sequence"] = []
        record = build_stage25_spec_acceptance(
            acceptance_id="ACCEPTANCE-STAGE25-002",
            spec=spec,
            approver="OWNER-1",
            rationale="Attempted acceptance.",
            evidence_refs=["control/master-codex-build-spec.json"],
            accepted_at="2026-08-23T12:00:00Z",
        )
        self.assertEqual(record["decision"], "rejected")

    def test_safety_fields_cannot_be_true(self):
        spec = load_master_spec()
        record = build_stage25_spec_acceptance(
            acceptance_id="ACCEPTANCE-STAGE25-003",
            spec=spec,
            approver="OWNER-1",
            rationale="Review complete.",
            evidence_refs=["control/master-codex-build-spec.json"],
            accepted_at="2026-08-23T12:00:00Z",
        )
        record["stage_advance_authorized"] = True
        validation = validate_stage25_spec_acceptance(record, spec=spec)
        self.assertEqual(validation["status"], "invalid")


if __name__ == "__main__":
    unittest.main()

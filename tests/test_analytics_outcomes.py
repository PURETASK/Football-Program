import tempfile
import unittest
from pathlib import Path

from nfl_fidos.analytics_outcomes import AnalyticsOutcomeService, build_outcome_observation
from nfl_fidos.repository import JsonRepository
from nfl_fidos.tenant_repository import TenantRepository


class AnalyticsOutcomeTests(unittest.TestCase):
    def setUp(self):
        self.tenant = TenantRepository(JsonRepository(Path(tempfile.mkdtemp()) / "state.json"), organization_id="ORG-OUTCOME", actor="ANALYST-1")

    def test_outcome_preserves_intent_actual_result_links_sample_and_uncertainty(self):
        service = AnalyticsOutcomeService(self.tenant)
        record = service.record(
            outcome_id="OUTCOME-1", intended_record_type="play_design", intended_record_id="PLAY-1", actual_result="success",
            success_count=7, sample_size=10, context={"situation": "third_down", "distance": "medium"}, evidence_refs=["FILM-OBS-1", "GAME-1"],
            recorded_by="ANALYST-1", linked_play_id="PLAY-1", practice_id="PRACTICE-1", film_observation_ids=["FILM-OBS-1"], game_plan_id="GAMEPLAN-1",
        )
        self.assertEqual(record["status"], "recorded")
        self.assertEqual(record["success_rate"], 0.7)
        self.assertEqual(record["confidence"], "moderate")
        self.assertEqual(record["uncertainty"]["method"], "wilson_95_percent")
        self.assertTrue(record["generalization_allowed"])
        summary = service.workspace(intended_record_id="PLAY-1")
        self.assertEqual(summary["total"], 1)
        self.assertEqual(summary["sample_size"], 10)
        self.assertFalse(summary["production_implementation_allowed"])

    def test_small_or_negative_outcomes_require_review_and_invalid_records_do_not_persist(self):
        service = AnalyticsOutcomeService(self.tenant)
        review = service.record(outcome_id="OUTCOME-2", intended_record_type="practice_period", intended_record_id="PERIOD-1", actual_result="failure", success_count=0, sample_size=2, context={"situation": "install"}, evidence_refs=["PRACTICE-1"], recorded_by="ANALYST-1")
        invalid = service.record(outcome_id="OUTCOME-3", intended_record_type="play_design", intended_record_id="PLAY-1", actual_result="success", success_count=4, sample_size=3, context={"situation": "third_down"}, evidence_refs=[], recorded_by="ANALYST-1")
        self.assertTrue(review["human_review_required"])
        self.assertFalse(review["generalization_allowed"])
        self.assertEqual(invalid["status"], "invalid")
        self.assertEqual(len(self.tenant.list("outcome_observations")), 1)

    def test_builder_requires_context_and_evidence(self):
        record = build_outcome_observation(outcome_id="OUTCOME-4", organization_id="ORG-OUTCOME", intended_record_type="play_design", intended_record_id="PLAY-1", actual_result="neutral", success_count=1, sample_size=1, context={}, evidence_refs=[], recorded_by="ANALYST-1")
        self.assertEqual(record["status"], "invalid")
        self.assertGreaterEqual(len(record["issues"]), 2)

    def test_workspace_aggregates_responsibility_phases_and_links(self):
        service = AnalyticsOutcomeService(self.tenant)
        service.record(outcome_id="OUTCOME-EXCHANGE", intended_record_type="play_design", intended_record_id="PLAY-1", actual_result="success", success_count=8, sample_size=10, context={"situation": "third_down"}, evidence_refs=["FILM-1"], recorded_by="ANALYST-1", linked_play_id="PLAY-1", linked_assignment_id="A-1", teaching_step_id="STEP-1", responsibility_phase="exchange")
        service.record(outcome_id="OUTCOME-READ", intended_record_type="play_design", intended_record_id="PLAY-1", actual_result="partial", success_count=3, sample_size=5, context={"situation": "third_down", "responsibility_phase": "read"}, evidence_refs=["FILM-2"], recorded_by="ANALYST-1", linked_play_id="PLAY-1", teaching_step_id="STEP-2")
        summary = service.workspace()["responsibility_phase_summary"]
        self.assertEqual([item["phase"] for item in summary], ["exchange", "read"])
        exchange = summary[0]
        self.assertEqual(exchange["success_count"], 8)
        self.assertEqual(exchange["sample_size"], 10)
        self.assertEqual(exchange["success_rate"], 0.8)
        self.assertEqual(exchange["linked_assignment_ids"], ["A-1"])
        self.assertEqual(summary[1]["human_review_required"], True)


if __name__ == "__main__":
    unittest.main()

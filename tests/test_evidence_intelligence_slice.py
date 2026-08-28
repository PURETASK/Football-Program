import tempfile
import unittest
from pathlib import Path

from nfl_fidos import FootballIntelligenceService, JsonRepository
from nfl_fidos.analytics_dictionary import calculate_metric
from nfl_fidos.film_intelligence import build_film_observation
from nfl_fidos.media import create_film_clip, register_film_asset
from nfl_fidos.scouting_intelligence import build_situational_scouting_report


def evidence_inputs():
    asset = register_film_asset(
        asset_id="FILM-SLICE-001", uri="authorized://film/001", duration_seconds=120,
        source={"kind": "licensed_film", "ref": "LICENSE-001"}, captured_at="2026-08-23", team_context="TEAM-1",
    )
    clip = create_film_clip(
        clip_id="CLIP-SLICE-001", asset=asset, start_seconds=10, end_seconds=18,
        team="TEAM-1", opponent="TEAM-2", situation="third_down",
    )
    observation = build_film_observation(
        observation_id="FILM-OBS-SLICE-001", clip_id=clip["id"], asset_id=asset["id"],
        domain="coverage", label="two_high", team="TEAM-1", opponent="TEAM-2",
        situation={"down": 3, "distance": 6}, source_frame="00:00:12.000",
        confidence="moderate", observed_or_inferred="observed", annotator="SCOUT-1",
        evidence="safety rotation is visible",
    )
    report = build_situational_scouting_report(
        report_id="SCOUT-REPORT-SLICE-001", opponent="TEAM-2", situation={"down": 3, "distance": "medium"},
        claims=[{"classification": "observed", "confidence": "moderate", "uncertainty": ["sample"], "evidence_refs": [clip["id"]]}],
        sample_size=12, source_refs=[clip["id"]], analyst="SCOUT-1",
    )
    metric = calculate_metric(
        definition={"id":"METRIC-DEF-THIRD-DOWN", "name":"third down success", "unit":"rate", "definition":"successes / attempts", "required_data":["success"], "formula":"successes / attempts", "context_dimensions":["down"], "caveats":["sample"], "validation_method":"reconcile", "consumers":["coach"]},
        numerator=7, denominator=12, context={"team":"TEAM-1", "opponent":"TEAM-2", "situation":"third_down"},
        source={"kind":"charting", "ref":clip["id"]}, observation_ids=[observation["id"]],
    )
    return asset, clip, observation, report, metric


class EvidenceIntelligenceSliceTests(unittest.TestCase):
    def test_package_persists_source_linked_review_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            package = service.create_evidence_intelligence_slice(
                asset=evidence_inputs()[0], clip=evidence_inputs()[1], observation=evidence_inputs()[2],
                scouting_report=evidence_inputs()[3], metric_observation=evidence_inputs()[4], analyst="SCOUT-1", qa_reviewer="COACH-1",
            )
            self.assertEqual(package["status"], "under_review")
            self.assertEqual(service.repository.get("film_clips", package["clip_id"])["asset_id"], package["asset_id"])
            self.assertEqual(service.repository.get("analytics_reports", package["analytics_report_id"])["status"], "draft")
            self.assertTrue(service.repository.history(collection="film_observations"))

    def test_low_quality_evidence_does_not_enter_package(self):
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            asset, clip, observation, report, metric = evidence_inputs()
            observation["confidence"] = "low"
            observation["classification"] = "inferred"
            with self.assertRaises(ValueError):
                service.create_evidence_intelligence_slice(
                    asset=asset, clip=clip, observation=observation, scouting_report=report,
                    metric_observation=metric, analyst="SCOUT-1", qa_reviewer="COACH-1",
                )
            self.assertEqual(len(service.repository.list("evidence_intelligence_slices")), 0)


if __name__ == "__main__":
    unittest.main()

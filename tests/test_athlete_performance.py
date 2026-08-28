import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos import build_performance_observation, build_readiness_summary


class AthletePerformanceTests(unittest.TestCase):
    def observation(self, observation_id="PERF-OBS-001", health_signal=False):
        return build_performance_observation(
            observation_id=observation_id, athlete_id="PLAYER-1", session_type="practice", duration_minutes=60,
            repetitions=40, quality_score=0.8, season_phase="regular_season", position="QB",
            source={"kind": "performance_log", "ref": observation_id}, health_signal=health_signal,
        )

    def test_observation_preserves_workload_quality_context_and_source(self):
        observation = self.observation()
        self.assertEqual(observation["status"], "valid")
        self.assertEqual(observation["workload"]["repetitions"], 40)
        self.assertEqual(observation["context"]["position"], "QB")

    def test_readiness_summary_requires_staff_review_with_sparse_data(self):
        summary = build_readiness_summary(summary_id="READINESS-001", athlete_id="PLAYER-1", observations=[self.observation()], signals=["quality stable"])
        self.assertEqual(summary["status"], "requires_staff_review")
        self.assertTrue(summary["staff_review_required"])
        self.assertIn("medical", summary["boundaries"][0])

    def test_health_signal_is_never_silently_normalized(self):
        summary = build_readiness_summary(summary_id="READINESS-002", athlete_id="PLAYER-1", observations=[self.observation(health_signal=True)], signals=[])
        self.assertEqual(summary["status"], "requires_staff_review")
        self.assertTrue(any("health-related" in signal for signal in summary["signals"]))

    def test_quality_out_of_bounds_is_rejected(self):
        observation = self.observation()
        invalid = build_performance_observation(
            observation_id=observation["id"], athlete_id=observation["athlete_id"], session_type=observation["session_type"],
            duration_minutes=60, repetitions=40, quality_score=1.2, season_phase="regular_season", position="QB", source=observation["source"],
        )
        self.assertEqual(invalid["status"], "rejected")


if __name__ == "__main__":
    unittest.main()

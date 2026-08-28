import json
import unittest
from pathlib import Path

from nfl_fidos.performance_bible import build_performance_support_plan, validate_performance_bible


class PerformanceBibleTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / "performance" / "performance-domain-bible.json"
        self.bible = json.loads(path.read_text(encoding="utf-8"))

    def test_bible_covers_domains_and_profiles(self):
        result = validate_performance_bible(self.bible)
        self.assertEqual(result["status"], "valid")
        self.assertGreaterEqual(result["profile_count"], 7)

    def test_support_plan_is_bounded_and_auditable(self):
        result = build_performance_support_plan(plan_id="PERF-PLAN-001", athlete_id="PLAYER-1", position="DB", season_phase="regular_season", week_context="week_1", objectives=[{"type":"acceleration","measure":"high-speed exposures"}], load_context={"practice_reps":40}, recovery_context={"sleep_hours":8}, source={"kind":"performance_log","ref":"LOG-1"}, reviewer="PERF-STAFF")
        self.assertEqual(result["status"], "under_review")
        self.assertFalse(result["staff_escalation_required"])
        self.assertTrue(result["boundaries"])

    def test_health_signal_escalates(self):
        result = build_performance_support_plan(plan_id="PERF-PLAN-002", athlete_id="PLAYER-1", position="RB", season_phase="regular_season", week_context="week_1", objectives=[{"type":"conditioning","measure":"repeat efforts"}], load_context={"practice_reps":20}, recovery_context={"pain_signal":True}, source={"kind":"performance_log","ref":"LOG-2"}, reviewer="PERF-STAFF")
        self.assertTrue(result["staff_escalation_required"])

    def test_medical_request_is_rejected(self):
        result = build_performance_support_plan(plan_id="PERF-PLAN-003", athlete_id="PLAYER-1", position="QB", season_phase="regular_season", week_context="week_1", objectives=[{"type":"diagnose","recommendation":"diagnosis"}], load_context={"practice_reps":1}, recovery_context={}, source={"kind":"note","ref":"NOTE-1"}, reviewer="PERF-STAFF")
        self.assertEqual(result["status"], "rejected")

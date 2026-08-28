import copy
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path

from nfl_fidos.rule_source_scheduler import RuleSourceScheduler


class RuleSourceSchedulerTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        self.registry = json.loads((root / "rules" / "authoritative-source-registry.json").read_text(encoding="utf-8"))

    def test_current_registry_has_no_due_sources_and_performs_no_fetch(self):
        result = RuleSourceScheduler().plan_due(registry=self.registry, now=datetime(2026, 8, 23, tzinfo=timezone.utc), freshness_days=30)
        self.assertEqual(result["status"], "current")
        self.assertEqual(result["due_count"], 0)
        self.assertFalse(result["fetch_performed"])
        self.assertFalse(result["promotion_allowed"])

    def test_stale_source_creates_bounded_human_review_work(self):
        stale = copy.deepcopy(self.registry)
        stale["sources"][0]["retrieved_at"] = "2026-01-01"
        result = RuleSourceScheduler().plan_due(registry=stale, now=datetime(2026, 8, 23, tzinfo=timezone.utc), freshness_days=30, max_sources=1)
        self.assertEqual(result["status"], "review_due")
        self.assertEqual(result["due_count"], 1)
        self.assertTrue(result["human_review_required"])
        self.assertFalse(result["promotion_allowed"])
        self.assertEqual(result["due_sources"][0]["candidate_status"], "proposed")

    def test_non_nfl_or_non_allowlisted_sources_are_blocked(self):
        invalid = copy.deepcopy(self.registry)
        invalid["jurisdiction"] = "NCAA"
        result = RuleSourceScheduler().plan_due(registry=invalid)
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(result["issues"])


if __name__ == "__main__":
    unittest.main()

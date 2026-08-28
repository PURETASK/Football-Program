import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from nfl_fidos.repository import JsonRepository
from nfl_fidos.source_connectors import SourceConnectorService
from nfl_fidos.source_scheduler import SourceRefreshScheduler
from nfl_fidos.tenant_repository import TenantRepository


class SourceSchedulerTests(unittest.TestCase):
    def test_due_plan_is_bounded_and_execution_persists_batch(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-SCHEDULER", actor="OWNER")
            connector = SourceConnectorService(repository, fetcher=lambda uri, limit: (b"fresh", {}))
            connector.register_source(source_id="SOURCE-SCHED-001", tier="tier_1_authoritative", kind="official_rulebook", uri="https://rules.example.test/one", captured_at="2026-08-23", effective_period="2026-season", citation_location="rule 1", owner="OWNER", allowed_domains=["rules.example.test"], freshness_days=1, actor="OWNER")
            connector.register_source(source_id="SOURCE-SCHED-002", tier="tier_1_authoritative", kind="official_rulebook", uri="https://rules.example.test/two", captured_at="2026-08-23", effective_period="2026-season", citation_location="rule 2", owner="OWNER", allowed_domains=["rules.example.test"], freshness_days=1, actor="OWNER")
            scheduler = SourceRefreshScheduler(repository, connector=connector)
            plan = scheduler.plan_due(now=datetime(2026, 8, 23, tzinfo=timezone.utc), max_sources=1)
            self.assertEqual(plan["due_count"], 2)
            self.assertEqual(len(plan["selected"]), 1)
            report = scheduler.run_due(actor="ANALYST", now=datetime(2026, 8, 23, tzinfo=timezone.utc), max_sources=1)
            self.assertEqual(report["refreshed_count"], 1)
            self.assertEqual(len(repository.list("source_refresh_batches")), 1)

    def test_current_schedule_has_no_destructive_action(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-SCHEDULER", actor="OWNER")
            report = SourceRefreshScheduler(repository).plan_due(max_sources=1)
            self.assertFalse(report["destructive_action_required"])
            self.assertEqual(report["status"], "current")


if __name__ == "__main__":
    unittest.main()

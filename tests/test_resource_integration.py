import unittest

from nfl_fidos.resource_integration import plan_resource_integration


class ResourceIntegrationTests(unittest.TestCase):
    def payload(self):
        return {
            "organization_id":"ORG-RESOURCE",
            "integration_id":"RESOURCE-INTEGRATION-001",
            "provider":{"kind":"calendar", "mode":"read_only", "source_ref":"SOURCE-CALENDAR-001"},
            "practice_id":"PRACTICE-RESOURCE-001",
            "schedule":{"schedule_id":"PRACTICE-SCHEDULE-001", "periods":[{"period_id":"PERIOD-1", "start":"2026-08-24T09:00:00+00:00", "end":"2026-08-24T09:30:00+00:00", "resource_ids":["FACILITY-1"]}]},
            "availability":[{"organization_id":"ORG-RESOURCE", "resource_id":"FACILITY-1", "available_from":"2026-08-24T08:00:00+00:00", "available_to":"2026-08-24T12:00:00+00:00"}],
        }

    def test_read_only_provider_produces_non_mutating_ready_plan(self):
        result = plan_resource_integration(**self.payload())
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["provider_action"], "read_availability_only")
        self.assertFalse(result["external_calendar_mutation"])
        self.assertFalse(result["external_state_changed"])

    def test_write_mode_and_bad_source_are_blocked(self):
        payload = self.payload()
        payload["provider"] = {"kind":"calendar", "mode":"write", "source_ref":"https://calendar.example"}
        result = plan_resource_integration(**payload)
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("read_only" in error for error in result["errors"]))
        self.assertTrue(any("approved SOURCE" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()

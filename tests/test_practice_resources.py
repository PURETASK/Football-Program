import copy
import unittest

from nfl_fidos.practice_resources import plan_practice_resources


class PracticeResourceTests(unittest.TestCase):
    def schedule(self):
        return {"schedule_id":"PRACTICE-SCHEDULE-001","timezone":"UTC","periods":[{"period_id":"PERIOD-1","start":"2026-08-24T09:00:00+00:00","end":"2026-08-24T09:30:00+00:00","resource_ids":["FACILITY-FIELD-1","STAFF-COACH-1"]}]}

    def availability(self):
        return [{"organization_id":"ORG-PRACTICE","resource_id":"FACILITY-FIELD-1","available_from":"2026-08-24T08:00:00+00:00","available_to":"2026-08-24T12:00:00+00:00"},{"organization_id":"ORG-PRACTICE","resource_id":"STAFF-COACH-1","available_from":"2026-08-24T09:00:00+00:00","available_to":"2026-08-24T10:00:00+00:00"}]

    def test_available_facility_and_staff_window_is_ready_without_external_mutation(self):
        result = plan_practice_resources(organization_id="ORG-PRACTICE", practice_id="PRACTICE-001", schedule=self.schedule(), availability=self.availability())
        self.assertEqual(result["status"], "ready")
        self.assertFalse(result["external_calendar_mutation"])

    def test_overlap_and_unavailable_resource_block_plan(self):
        schedule = copy.deepcopy(self.schedule())
        schedule["periods"].append({"period_id":"PERIOD-2","start":"2026-08-24T09:15:00+00:00","end":"2026-08-24T09:45:00+00:00","resource_ids":["FACILITY-FIELD-1","STAFF-COACH-2"]})
        result = plan_practice_resources(organization_id="ORG-PRACTICE", practice_id="PRACTICE-001", schedule=schedule, availability=self.availability())
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any(conflict["type"] == "scheduled_overlap" for conflict in result["conflicts"]))
        self.assertTrue(any(conflict["type"] == "resource_unavailable" for conflict in result["conflicts"]))

    def test_cross_organization_availability_is_rejected(self):
        availability = self.availability()
        availability[0]["organization_id"] = "ORG-OTHER"
        result = plan_practice_resources(organization_id="ORG-PRACTICE", practice_id="PRACTICE-001", schedule=self.schedule(), availability=availability)
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("scope mismatch" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()

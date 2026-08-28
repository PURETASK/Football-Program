import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.repository import JsonRepository
from nfl_fidos.service import FootballIntelligenceService


class PracticeApiTests(unittest.TestCase):
    def test_coach_creates_and_reads_practice_workspace(self):
        secret = "practice-api-test-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        coach = {"Authorization": "Bearer " + issue_token(subject="COACH-PRACTICE-API", role="coach_staff", organization_id="ORG-PRACTICE-API", secret=secret)}
        player = {"Authorization": "Bearer " + issue_token(subject="PLAYER-PRACTICE-API", role="player", organization_id="ORG-PRACTICE-API", secret=secret)}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            body = {"organization_id":"ORG-PRACTICE-API", "practice_id":"PRACTICE-API-001", "team_context":"TEAM-1", "season_phase":"regular_season", "week_context":"WEEK-1", "objective":"fit run", "opponent_priorities":["gap run"], "periods":[{"id":"PERIOD-API-1", "type":"team", "objective":"fit", "owner":"COACH", "players":["DL"], "minutes":20, "reps":8, "learning_rationale":"leverage", "load_rationale":"moderate", "play_ids":["PLAY-1"], "drill_ids":["DRILL-1"]}], "staff_available":["COACH"], "facility_constraints":[], "load_controls":{"max_total_minutes":30, "max_reps_by_position":{"DL":20}}, "restrictions":[], "roster_ids":["PLAYER-1"], "install_items":[{"period_id":"PERIOD-API-1", "play_ids":["PLAY-1"], "drill_ids":["DRILL-1"]}], "attendance_policy":"coach_confirmed"}
            status, _ = handle_request(method="POST", path="/v1/practice/plans", body=body, headers=coach, service=service)
            self.assertEqual(status, 201)
            status, payload = handle_request(method="GET", path="/v1/practice/workspace?organization_id=ORG-PRACTICE-API&week=WEEK-1", headers=coach, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["plans"][0]["id"], "PRACTICE-API-001")
            self.assertEqual(payload["data"]["plans"][0]["roster_ids"], ["PLAYER-1"])
            self.assertEqual(payload["data"]["plans"][0]["install_items"][0]["play_ids"], ["PLAY-1"])
            self.assertEqual(payload["data"]["plans"][0]["attendance_policy"], "coach_confirmed")
            service.repository.put("drills", "DRILL-CATALOG-1", {"id": "DRILL-CATALOG-1", "organization_id": "ORG-PRACTICE-API", "name": "QB pressure escape", "skill": "pressure recognition", "position_groups": ["QB"], "status": "approved"}, actor="COACH-PRACTICE-API", reason="fixture")
            status, payload = handle_request(method="GET", path="/v1/practice/drills?organization_id=ORG-PRACTICE-API&position_group=QB&search=pressure", headers=coach, service=service)
            self.assertEqual(status, 200)
            self.assertEqual([drill["id"] for drill in payload["data"]["drills"]], ["DRILL-CATALOG-1"])
            self.assertEqual(handle_request(method="GET", path="/v1/practice/workspace?organization_id=ORG-PRACTICE-API", headers=player, service=service)[0], 403)
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

    def test_coach_can_run_read_only_resource_preflight(self):
        secret = "practice-resource-api-test-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        headers = {"Authorization": "Bearer " + issue_token(subject="COACH-RESOURCE-API", role="coach_staff", organization_id="ORG-RESOURCE-API", secret=secret)}
        body = {
            "organization_id":"ORG-RESOURCE-API",
            "integration_id":"RESOURCE-INTEGRATION-API-001",
            "provider":{"kind":"facility_system", "mode":"read_only", "source_ref":"PROVIDER-FACILITY-001"},
            "practice_id":"PRACTICE-RESOURCE-API-001",
            "schedule":{"schedule_id":"PRACTICE-SCHEDULE-API-001", "periods":[{"period_id":"PERIOD-API-1", "start":"2026-08-24T09:00:00+00:00", "end":"2026-08-24T09:30:00+00:00", "resource_ids":["FIELD-1"]}]},
            "availability":[{"organization_id":"ORG-RESOURCE-API", "resource_id":"FIELD-1", "available_from":"2026-08-24T08:00:00+00:00", "available_to":"2026-08-24T12:00:00+00:00"}],
        }
        status, payload = handle_request(method="POST", path="/v1/practice/resources/preflight", headers=headers, body=body, service=FootballIntelligenceService(JsonRepository(Path.cwd() / ".runtime" / "resource-api-test-state.json")))
        self.assertEqual(status, 200)
        self.assertEqual(payload["data"]["status"], "ready")
        self.assertFalse(payload["data"]["external_state_changed"])
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)


if __name__ == "__main__":
    unittest.main()

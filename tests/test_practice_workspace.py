import tempfile
import unittest
from pathlib import Path

from nfl_fidos.practice_workspace import PracticeWorkspaceService
from nfl_fidos.repository import JsonRepository
from nfl_fidos.tenant_repository import TenantRepository


class PracticeWorkspaceTests(unittest.TestCase):
    def test_valid_plan_persists_and_load_exceeded_is_visible(self):
        with tempfile.TemporaryDirectory() as directory:
            service = PracticeWorkspaceService(TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-PRACTICE", actor="COACH"))
            period = {"id":"PERIOD-1", "type":"team", "objective":"fit run", "owner":"COACH", "players":["DL"], "minutes":20, "reps":8, "learning_rationale":"fit with leverage", "load_rationale":"moderate"}
            plan = service.create_plan(practice_id="PRACTICE-001", team_context="TEAM-1", season_phase="regular_season", week_context="WEEK-1", objective="install run fits", opponent_priorities=["gap run"], periods=[period], staff_available=["COACH"], facility_constraints=[], load_controls={"max_total_minutes":30, "max_reps_by_position":{"DL":20}}, restrictions=[], actor="COACH")
            self.assertEqual(plan["status"], "draft")
            workspace = service.workspace(week="WEEK-1")
            self.assertEqual(workspace["status"], "ready")
            self.assertEqual(workspace["load_exceeded"], 0)
            bad = service.create_plan(practice_id="PRACTICE-002", team_context="TEAM-1", season_phase="regular_season", week_context="WEEK-1", objective="install", opponent_priorities=["pressure"], periods=[{**period, "minutes":40}], staff_available=["COACH"], facility_constraints=[], load_controls={"max_total_minutes":30, "max_reps_by_position":{"DL":20}}, restrictions=[], actor="COACH")
            self.assertEqual(bad["status"], "invalid")


if __name__ == "__main__":
    unittest.main()

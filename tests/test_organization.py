import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos import build_organization_context, resolve_person


class OrganizationTests(unittest.TestCase):
    def context(self):
        return build_organization_context(
            organization_id="ORG-001", name="Example NFL Organization", season="2026",
            people=[
                {"id": "PLAYER-1", "name": "Player One", "type": "player", "position": "QB"},
                {"id": "COACH-1", "name": "Coach One", "type": "coach", "staff_role": "position_coach"},
            ], terminology_version="TERM-0.1.0", owner="program-owner", source={"kind": "team_system", "ref": "ORG-SOURCE-001"},
        )

    def test_organization_context_is_nfl_scoped_and_versioned(self):
        context = self.context()
        self.assertEqual(context["status"], "draft")
        self.assertEqual(context["league"], "NFL")
        self.assertEqual(context["terminology_version"], "TERM-0.1.0")

    def test_person_resolution_preserves_season_and_org(self):
        context = self.context()
        result = resolve_person(context, "PLAYER-1")
        self.assertEqual(result["status"], "resolved")
        self.assertEqual(result["season"], "2026")
        self.assertEqual(result["person"]["position"], "QB")

    def test_unknown_person_requires_review(self):
        result = resolve_person(self.context(), "PLAYER-UNKNOWN")
        self.assertEqual(result["status"], "unresolved")
        self.assertTrue(result["requires_review"])

    def test_invalid_staff_role_and_player_position_reject_context(self):
        context = self.context()
        people = context["people"] + [
            {"id": "PLAYER-2", "name": "Player Two", "type": "player"},
            {"id": "STAFF-2", "name": "Staff Two", "type": "staff", "staff_role": "unknown"},
        ]
        result = build_organization_context(
            organization_id=context["id"], name=context["name"], season=context["season"], people=people,
            terminology_version=context["terminology_version"], owner=context["owner"], source=context["source"],
        )
        codes = {issue["code"] for issue in result["issues"]}
        self.assertEqual(result["status"], "rejected")
        self.assertTrue({"ORG-PLAYER-POSITION", "ORG-STAFF-ROLE"}.issubset(codes))


if __name__ == "__main__":
    unittest.main()

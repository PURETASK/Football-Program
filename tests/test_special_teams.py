import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos import build_special_teams_plan


class SpecialTeamsTests(unittest.TestCase):
    def plan(self):
        return build_special_teams_plan(
            plan_id="ST-001", unit="punt", phase="coverage", operation="cover punt",
            roles=[{"role": "gunner", "responsibility": "release and cover"}, {"role": "protector", "responsibility": "protect operation"}],
            situations=["normal_punt", "backed_up"], constraints=["team terminology"], source={"kind": "team_playbook", "ref": "ST-PB-001"},
        )

    def test_special_teams_plan_is_explicit_and_traceable(self):
        plan = self.plan()
        self.assertEqual(plan["status"], "draft")
        self.assertEqual(plan["unit"], "punt")
        self.assertEqual(plan["source"]["ref"], "ST-PB-001")
        self.assertTrue(plan["review_required"])

    def test_special_teams_rejects_unknown_phase(self):
        plan = self.plan()
        plan["phase"] = "unknown"
        result = build_special_teams_plan(
            plan_id=plan["id"], unit=plan["unit"], phase=plan["phase"], operation=plan["operation"], roles=plan["roles"], situations=plan["situations"], constraints=plan["constraints"], source=plan["source"],
        )
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["issues"][0]["code"], "ST-PHASE")

    def test_special_teams_rejects_duplicate_role_assignments(self):
        plan = self.plan()
        roles = plan["roles"] + [{"role": "gunner", "responsibility": "alternate"}]
        result = build_special_teams_plan(
            plan_id=plan["id"], unit=plan["unit"], phase=plan["phase"], operation=plan["operation"], roles=roles, situations=plan["situations"], constraints=plan["constraints"], source=plan["source"],
        )
        self.assertTrue(any(issue["code"] == "ST-DUPLICATE-ROLE" for issue in result["issues"]))


if __name__ == "__main__":
    unittest.main()

import unittest

from nfl_fidos.playbook_architecture import (
    approve_play,
    build_extended_play,
    build_play_family,
    extract_role_play_spec,
    request_play_approval,
    validate_play_spec,
)


def play():
    return {
        "id":"PLAY-SPEC-001", "version":"0.1.0", "team_context":"TEAM-1",
        "situation":{"down":3,"distance":6,"field_zone":"open_field"}, "personnel":"11", "formation":"shotgun",
        "assignments":[{"role":"QB","assignment":"read","responsibility":"read safety"},{"role":"C","assignment":"block","responsibility":"set protection"}],
        "source":{"kind":"team_playbook","ref":"PB-1"}, "status":"draft",
    }


class PlaybookArchitectureTests(unittest.TestCase):
    def test_extended_play_compiles_and_extracts_role_spec(self):
        result = build_extended_play(play(), play_family_id="PLAY-FAM-001", install_level="install", checks=[{"role":"QB","text":"confirm rotation"}], situational_variants=[{"situation":"third_down","variant":"hot"}], opponent_notes=["check pressure"], coaching_notes=["eyes before feet"], dependencies=["SCHEME-001"])
        self.assertEqual(result["status"], "draft")
        view = extract_role_play_spec(result, role="QB")
        self.assertEqual(view["status"], "renderable")
        self.assertEqual(view["assignment"]["responsibility"], "read safety")

    def test_publish_requires_human_approval(self):
        extended = build_extended_play(play(), play_family_id="PLAY-FAM-001", install_level="game_ready", checks=[], situational_variants=[], opponent_notes=[], coaching_notes=[], dependencies=[])
        pending = request_play_approval(extended, requester="COACH", decision_ref="DEC-PLAY-1")
        self.assertEqual(pending["approval"]["state"], "pending_approval")
        approved = approve_play(pending, approver="OWNER", decision_ref="DEC-PLAY-1")
        self.assertEqual(approved["approval"]["state"], "approved")
        self.assertEqual(approved["status"], "locked")

    def test_family_requires_owner_and_variants(self):
        with self.assertRaises(ValueError):
            build_play_family(family_id="PLAY-FAM-001", name="x", unit="offense", concept_ids=["x"], variants=[], owner="OWNER")

    def test_extended_spec_rejects_missing_responsibility(self):
        source = play()
        source["assignments"][0].pop("responsibility")
        extended = build_extended_play(source, play_family_id="PLAY-FAM-001", install_level="install", checks=[], situational_variants=[], opponent_notes=[], coaching_notes=[], dependencies=[])
        self.assertTrue(any(issue["code"] == "PLAY-RESPONSIBILITY" for issue in validate_play_spec(extended)))

import tempfile
import unittest
import os
from pathlib import Path

from nfl_fidos import FootballIntelligenceService, JsonRepository, handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.playbook_architecture import build_extended_play
from test_play_compiler import valid_play


def extended_play():
    source = valid_play()
    responsibilities = {
        "QB": "read coverage",
        "RB": "check release",
        "WR": "win leverage",
        "C": "set protection",
    }
    for assignment in source["assignments"]:
        assignment["responsibility"] = responsibilities.get(assignment["role"], "execute assignment")
    return build_extended_play(
        source,
        play_family_id="PLAY-FAM-001",
        install_level="game_ready",
        checks=[{"role": "QB", "text": "confirm rotation"}],
        situational_variants=[{"situation": "third_down", "variant": "hot"}],
        opponent_notes=["check pressure"],
        coaching_notes=["eyes before feet"],
        dependencies=["SCHEME-001"],
    )


def drill():
    return {
        "id": "DRILL-SLICE-001",
        "name": "Read and replace",
        "drill_type": "individual",
        "position": "QB",
        "target_skill": "coverage recognition",
        "competencies": ["CAP-003"],
        "classification": {"contact_level": "non_contact", "decision_load": "high"},
        "setup": {"space": "half_field"},
        "dose": {"minutes": 8, "reps": 12, "intensity": "moderate"},
        "coaching_cues": ["eyes before feet"],
        "common_errors": ["late confirmation"],
        "corrections": ["reset vision"],
        "kpis": [{"name": "correct_read_rate", "target": 0.8}],
        "regressions": ["static shell"],
        "progressions": ["add rotation"],
        "film_angles": ["wide"],
        "safety": {"controls": ["no contact", "hydration"]},
    }


class CorePlaySliceTests(unittest.TestCase):
    def test_slice_persists_role_view_drill_and_pending_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = JsonRepository(Path(directory) / "state.json")
            service = FootballIntelligenceService(repository)
            package = service.create_core_play_slice(
                play=extended_play(), role="QB", drill=drill(), actor="coach-1", decision_ref="DEC-SLICE-001"
            )
            self.assertEqual(package["status"], "pending_approval")
            self.assertEqual(repository.get("play_views", package["play_view_id"])["status"], "renderable")
            self.assertEqual(repository.get("drills", package["drill_id"])["kpis"][0]["name"], "correct_read_rate")
            self.assertGreaterEqual(len(repository.history(record_id="PLAY-001")), 1)

    def test_approval_publishes_locked_play_and_records_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = JsonRepository(Path(directory) / "state.json")
            service = FootballIntelligenceService(repository)
            service.create_core_play_slice(
                play=extended_play(), role="QB", drill=drill(), actor="coach-1", decision_ref="DEC-SLICE-001"
            )
            package = service.approve_core_play_slice(play_id="PLAY-001", approver="program-owner", decision_ref="DEC-SLICE-001")
            self.assertEqual(package["status"], "approved")
            self.assertEqual(repository.get("plays", "PLAY-001")["approval"]["state"], "approved")
            self.assertEqual(repository.get("plays", "PLAY-001")["status"], "locked")
            self.assertEqual(len(repository.history(collection="plays")), 1)

    def test_api_exposes_injected_core_slice_service(self):
        with tempfile.TemporaryDirectory() as directory:
            os.environ["NFL_FIDOS_AUTH_SECRET"] = "test-secret"
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            headers = {"Authorization": "Bearer " + issue_token(subject="coach-1", role="coach_staff", organization_id="ORG-1", secret="test-secret")}
            status, response = handle_request(
                method="POST",
                path="/v1/workflows/core-play",
                body={"play": extended_play(), "role": "QB", "drill": drill(), "decision_ref": "DEC-SLICE-001", "organization_id":"ORG-1"},
                service=service,
                headers=headers,
            )
            self.assertEqual(status, 201)
            self.assertEqual(response["data"]["status"], "pending_approval")
            status, response = handle_request(
                method="POST",
                path="/v1/workflows/core-play/PLAY-001/approve",
                body={"approver": "program-owner", "decision_ref": "DEC-SLICE-001", "organization_id":"ORG-1"},
                service=service,
                headers={"Authorization": "Bearer " + issue_token(subject="owner-1", role="program_owner", organization_id="ORG-1", secret="test-secret")},
            )
            self.assertEqual(status, 200)
            self.assertEqual(response["data"]["status"], "approved")


if __name__ == "__main__":
    unittest.main()

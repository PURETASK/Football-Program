import tempfile
import unittest
from pathlib import Path

from nfl_fidos.film_room_service import FilmRoomService
from nfl_fidos.film_intelligence import build_film_observation
from nfl_fidos.repository import JsonRepository
from nfl_fidos.tenant_repository import TenantRepository


def observation():
    record = build_film_observation(observation_id="FILM-OBS-SVC-001", clip_id="CLIP-SVC-001", asset_id="FILM-SVC-001", domain="coverage", label="two_high", team="TEAM-1", opponent="TEAM-2", situation={"down":3}, source_frame="00:00:02.000", confidence="moderate", observed_or_inferred="observed", annotator="SCOUT-1", evidence="rotation visible")
    record["organization_id"] = "ORG-1"
    return record


class FilmRoomServiceTests(unittest.TestCase):
    def test_search_survives_service_recreation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            first = FilmRoomService(TenantRepository(JsonRepository(path), organization_id="ORG-1", actor="SCOUT-1"))
            first.save_observation(observation(), actor="SCOUT-1")
            second = FilmRoomService(TenantRepository(JsonRepository(path), organization_id="ORG-1", actor="COACH-1"))
            self.assertEqual(len(second.search(opponent="TEAM-2")), 1)

    def test_observation_preserves_governed_downstream_workflow_links(self):
        with tempfile.TemporaryDirectory() as directory:
            service = FilmRoomService(TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-1", actor="SCOUT-1"))
            record = observation()
            record["linked_record_refs"] = [
                {"record_type": "scouting", "record_id": "SCOUT-REPORT-1"},
                {"type": "game_plan", "id": "GAMEPLAN-1", "label": "Third-down answer"},
                {"record_type": "player_development", "record_id": "ASSIGNMENT-1"},
            ]
            saved = service.save_observation(record, actor="SCOUT-1")
            self.assertEqual([link["record_type"] for link in saved["linked_record_refs"]], ["scouting", "game_plan", "player_development"])
            invalid = observation()
            invalid["id"] = "FILM-OBS-SVC-002"
            invalid["linked_record_refs"] = [{"record_type": "unapproved_workspace", "record_id": "X-1"}]
            with self.assertRaises(ValueError):
                service.save_observation(invalid, actor="SCOUT-1")

    def test_quiz_attempt_is_persisted_and_scoped(self):
        with tempfile.TemporaryDirectory() as directory:
            service = FilmRoomService(TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-1", actor="COACH-1"))
            service.create_quiz(quiz_id="QUIZ-SVC-001", title="Coverage", role="QB", clip_ids=["CLIP-SVC-001"], questions=[{"id":"Q-1", "prompt":"shell", "expected_answer":"two_high", "evidence_refs":["CLIP-SVC-001"]}], owner="COACH-1", actor="COACH-1")
            attempt = service.submit_quiz(attempt_id="QUIZ-ATTEMPT-SVC-001", quiz_id="QUIZ-SVC-001", participant="PLAYER-1", answers={"Q-1":"two_high"}, actor="PLAYER-1")
            self.assertEqual(attempt["score"], 1.0)
            self.assertEqual(len(service.repository.list("film_quiz_attempts")), 1)

    def test_bounded_voice_note_is_clip_linked_and_role_filtered(self):
        with tempfile.TemporaryDirectory() as directory:
            tenant = TenantRepository(JsonRepository(Path(directory) / "state.json"), organization_id="ORG-1", actor="COACH-1")
            tenant.put("film_clips", "CLIP-VOICE-001", {"id": "CLIP-VOICE-001", "organization_id": "ORG-1", "asset_id": "FILM-VOICE-001"}, actor="SEED", reason="fixture")
            service = FilmRoomService(tenant)
            note = service.create_voice_note(note_id="VOICE-NOTE-001", clip_id="CLIP-VOICE-001", frame_seconds=2.25, mime_type="audio/webm", audio_data="data:audio/webm;base64,AAE=", transcript="Watch the safety rotate.", access_roles=["coach_staff"], author="COACH-1", actor="COACH-1")
            self.assertEqual(note["byte_size"], 2)
            self.assertEqual(note["clip_id"], "CLIP-VOICE-001")
            self.assertEqual(len(service.list_voice_notes(role="coach_staff")), 1)
            self.assertEqual(service.list_voice_notes(role="analyst"), [])
            with self.assertRaises(ValueError):
                service.create_voice_note(note_id="VOICE-NOTE-002", clip_id="CLIP-VOICE-001", frame_seconds=2.25, mime_type="text/plain", audio_data="data:text/plain;base64,AAE=", transcript="Bad media", access_roles=[], author="COACH-1", actor="COACH-1")


if __name__ == "__main__":
    unittest.main()

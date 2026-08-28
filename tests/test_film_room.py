import unittest

from nfl_fidos.film_intelligence import build_film_observation
from nfl_fidos.film_room import FilmRoomIndex, append_annotation, build_annotation_session, build_film_quiz, submit_film_quiz


def observation(organization_id="ORG-1"):
    result = build_film_observation(observation_id="FILM-OBS-ROOM-001", clip_id="CLIP-ROOM-001", asset_id="FILM-ROOM-001", domain="coverage", label="two_high", team="TEAM-1", opponent="TEAM-2", situation={"down":3}, source_frame="00:00:02.000", confidence="moderate", observed_or_inferred="observed", annotator="SCOUT-1", evidence="rotation visible")
    result["organization_id"] = organization_id
    return result


class FilmRoomTests(unittest.TestCase):
    def test_search_is_scoped_and_contextual(self):
        index = FilmRoomIndex(organization_id="ORG-1")
        index.add(observation())
        self.assertEqual(len(index.search(opponent="TEAM-2", label="two_high")), 1)
        with self.assertRaises(PermissionError):
            index.add({**observation("ORG-2"), "id":"FILM-OBS-ROOM-002"})

    def test_annotation_session_flags_correction(self):
        session = build_annotation_session(session_id="ANNOTATION-001", clip_id="CLIP-ROOM-001", organization_id="ORG-1", annotator="SCOUT-1", allowed_domains=["coverage"], source_refs=["CLIP-ROOM-001"])
        result = append_annotation(session=session, observation={**observation(), "confidence":"low", "status":"needs_review"})
        self.assertTrue(result["correction_required"])

    def test_quiz_grades_answers_with_evidence_and_review(self):
        quiz = build_film_quiz(quiz_id="QUIZ-001", title="Third-down rotation", organization_id="ORG-1", role="QB", clip_ids=["CLIP-ROOM-001"], questions=[{"id":"Q-1", "prompt":"What shell is shown?", "expected_answer":"two_high", "evidence_refs":["CLIP-ROOM-001"]}], owner="COACH-1")
        attempt = submit_film_quiz(attempt_id="QUIZ-ATTEMPT-001", quiz=quiz, participant="PLAYER-1", answers={"Q-1":"two_high"})
        self.assertEqual(attempt["score"], 1.0)
        self.assertEqual(attempt["status"], "under_review")


if __name__ == "__main__":
    unittest.main()

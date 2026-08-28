import unittest

from nfl_fidos.film_intelligence import build_assignment_grade, build_film_observation, build_film_playlist, correct_film_observation, validate_film_qa


def observation():
    return build_film_observation(observation_id="FILM-OBS-001", clip_id="CLIP-001", asset_id="FILM-001", domain="coverage", label="two_high", team="TEAM-1", opponent="TEAM-2", situation={"down":3,"distance":6}, source_frame="00:01:02.100", confidence="moderate", observed_or_inferred="observed", annotator="SCOUT", evidence="safety rotation visible")


class FilmIntelligenceTests(unittest.TestCase):
    def test_observation_is_traceable_and_correctable(self):
        item = observation()
        self.assertEqual(item["status"], "ready_for_review")
        corrected = correct_film_observation(observation=item, corrected_label="quarters", corrected_by="COACH", reason="reviewed end-zone angle")
        self.assertEqual(corrected["status"], "corrected")
        self.assertEqual(corrected["correction"]["corrected_by"], "COACH")

    def test_low_confidence_inference_cannot_receive_definitive_grade(self):
        result = build_assignment_grade(grade_id="GRADE-001", observation=observation(), player_id="PLAYER-1", assignment="carry seam", grade="plus", assignment_basis="inferred", confidence="low", evidence_refs=["FILM-OBS-001"], grader="COACH")
        self.assertEqual(result["status"], "needs_review")

    def test_playlist_and_qa_preserve_clip_provenance(self):
        playlist = build_film_playlist(playlist_id="PLAYLIST-001", name="Third down", purpose="teaching", clip_ids=["CLIP-001"], filters={"situation":"third_down"}, owner="COACH", access_roles=["coach_staff"])
        self.assertEqual(playlist["status"], "draft")
        qa = validate_film_qa(qa_id="FILM-QA-001", clips=[{"id":"CLIP-001","status":"ready"}], observations=[observation()], reviewer="QA")
        self.assertEqual(qa["status"], "passed")

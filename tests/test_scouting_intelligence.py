import unittest

from nfl_fidos.scouting_intelligence import build_matchup_model, build_opponent_evolution, build_opponent_profile, build_situational_scouting_report


class ScoutingIntelligenceTests(unittest.TestCase):
    def profile(self, source_kind="licensed_film"):
        return build_opponent_profile(profile_id="OPP-PROFILE-001", opponent="OPP-1", season="2026", schedule_context={"week":1,"venue":"away"}, roster_context={"source":"public"}, offense={"formations":[]}, defense={"coverages":[]}, special_teams={"units":[]}, sources=[{"kind":source_kind,"ref":"FILM-1","captured_at":"2026-08-23"}])

    def test_profile_requires_authorized_provenance(self):
        self.assertEqual(self.profile()["status"], "draft")
        self.assertEqual(self.profile("unauthorized_source")["status"], "invalid")

    def test_situational_claims_require_classification_and_uncertainty(self):
        report = build_situational_scouting_report(report_id="SCOUT-REPORT-001", opponent="OPP-1", situation={"down":3,"distance":"medium"}, claims=[{"classification":"observed","confidence":"moderate","uncertainty":["sample"],"evidence_refs":["FILM-1"]}], sample_size=8, source_refs=["FILM-1"], analyst="SCOUT")
        self.assertEqual(report["status"], "under_review")

    def test_matchup_and_evolution_retain_human_review(self):
        matchup = build_matchup_model(model_id="MATCHUP-001", opponent="OPP-1", matchups=[{"our_role":"WR1","opponent_role":"CB1","advantage_hypothesis":"release","counter":"stack","uncertainty":"small sample"}], evidence_refs=["FILM-1"], context={"situation":"third_down"}, analyst="SCOUT")
        self.assertTrue(matchup["human_review_required"])
        evolution = build_opponent_evolution(evolution_id="EVOLUTION-001", opponent="OPP-1", historical_claims=[{"claim":"A"}], current_claims=[{"claim":"B"}], evidence_refs=["FILM-1"], analyst="SCOUT")
        self.assertEqual(evolution["status"], "under_review")

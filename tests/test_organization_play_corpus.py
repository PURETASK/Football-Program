import unittest

from nfl_fidos.organization_play_corpus import approve_organization_play_corpus, build_organization_play_corpus


def valid_play():
    return {"id":"PLAY-ORG-001","version":"0.1.0","unit":"offense","team_context":"TEAM-ORG-1","situation":{"down":1,"distance":10,"field_zone":"open_field"},"personnel":"11","formation":"shotgun","assignments":[{"role":"QB","assignment":"read shell"},{"role":"C","assignment":"set protection"}],"source":{"kind":"team_playbook","ref":"AUTH-SOURCE-001"},"status":"draft"}


class OrganizationPlayCorpusTests(unittest.TestCase):
    def test_valid_corpus_compiles_and_owner_can_validate(self):
        corpus = build_organization_play_corpus(corpus_id="ORG-PLAY-CORPUS-001", organization_id="ORG-1", team_context="TEAM-ORG-1", season="2026", plays=[valid_play()], source_refs=["AUTH-SOURCE-001"], compiler="COACH-1")
        self.assertEqual(corpus["status"], "under_review")
        approved = approve_organization_play_corpus(corpus=corpus, approver="OWNER-1", approver_role="program_owner", decision_ref="DEC-PLAY-001")
        self.assertEqual(approved["status"], "validated")
        self.assertFalse(approved["production_implementation_allowed"])

    def test_team_and_source_context_are_enforced(self):
        play = valid_play()
        play["team_context"] = "TEAM-OTHER"
        play["source"]["ref"] = "UNAUTHORIZED"
        corpus = build_organization_play_corpus(corpus_id="ORG-PLAY-CORPUS-002", organization_id="ORG-1", team_context="TEAM-ORG-1", season="2026", plays=[play], source_refs=["AUTH-SOURCE-001"], compiler="COACH-1")
        self.assertEqual(corpus["status"], "rejected")
        self.assertTrue(any(issue["code"] == "ORG-PLAY-TEAM" for issue in corpus["issues"]))
        self.assertTrue(any(issue["code"] == "ORG-PLAY-SOURCE-LINK" for issue in corpus["issues"]))


if __name__ == "__main__":
    unittest.main()

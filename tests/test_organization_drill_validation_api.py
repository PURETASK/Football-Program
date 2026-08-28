import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos import FootballIntelligenceService, JsonRepository, handle_request
from nfl_fidos.auth import issue_token


class OrganizationDrillValidationApiTests(unittest.TestCase):
    def test_coach_can_submit_under_review_package_and_player_cannot(self):
        secret = "org-drill-api-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        coach = {"Authorization": "Bearer " + issue_token(subject="COACH-1", role="coach_staff", organization_id="ORG-DRILL-API", secret=secret)}
        owner = {"Authorization": "Bearer " + issue_token(subject="OWNER-1", role="program_owner", organization_id="ORG-DRILL-API", secret=secret)}
        player = {"Authorization": "Bearer " + issue_token(subject="PLAYER-1", role="player", organization_id="ORG-DRILL-API", secret=secret)}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            body = {"organization_id":"ORG-DRILL-API","validation_id":"ORG-DRILL-VALIDATION-API-001","season":"2026","position":"QB","selected_drill_ids":["DRILL-QB-001","VARIANT-DRILL-QB-OFFSEASON-001"],"source_refs":["AUTH-SOURCE-001"]}
            status, response = handle_request(method="POST", path="/v1/practice/drill-validation", body=body, headers=coach, service=service)
            self.assertEqual(status, 201)
            self.assertEqual(response["data"]["status"], "under_review")
            status, response = handle_request(method="POST", path="/v1/practice/drill-validation/approve", body={"organization_id":"ORG-DRILL-API","validation_id":"ORG-DRILL-VALIDATION-API-001","decision_ref":"DEC-DRILL-API-001"}, headers=owner, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(response["data"]["status"], "validated")
            self.assertFalse(response["data"]["production_implementation_allowed"])
            status, response = handle_request(method="GET", path="/v1/practice/drill-validation?organization_id=ORG-DRILL-API", headers=coach, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(len(response["data"]["packages"]), 1)
            self.assertEqual(handle_request(method="GET", path="/v1/practice/drill-validation?organization_id=ORG-DRILL-API", headers=player, service=service)[0], 403)
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)


if __name__ == "__main__":
    unittest.main()

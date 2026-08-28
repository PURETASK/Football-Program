import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos import FootballIntelligenceService, JsonRepository, handle_request
from nfl_fidos.auth import issue_token


class AuthorizedSourceApiTests(unittest.TestCase):
    def setUp(self):
        self.secret = "authorized-source-api-secret-012345678901234567890"
        self.previous_secret = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        os.environ["NFL_FIDOS_AUTH_SECRET"] = self.secret
        self.temp_directory = tempfile.TemporaryDirectory()
        self.service = FootballIntelligenceService(JsonRepository(Path(self.temp_directory.name) / "state.json"))
        self.owner = {"Authorization": "Bearer " + issue_token(subject="OWNER-SOURCE", role="program_owner", organization_id="ORG-SOURCE-API", secret=self.secret)}
        self.analyst = {"Authorization": "Bearer " + issue_token(subject="ANALYST-SOURCE", role="analyst", organization_id="ORG-SOURCE-API", secret=self.secret)}

    def tearDown(self):
        self.temp_directory.cleanup()
        if self.previous_secret is None:
            os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
        else:
            os.environ["NFL_FIDOS_AUTH_SECRET"] = self.previous_secret

    def _body(self):
        return {"organization_id":"ORG-SOURCE-API","authorization":{"authorization_id":"AUTH-SOURCE-API-001","organization_id":"ORG-SOURCE-API","source_id":"SOURCE-API-001","uri":"https://approved.example.invalid/team-doc","license_class":"team_authorized","authorization_ref":"DEC-SOURCE-API-001","approved_by":"OWNER-SOURCE","approved_at":"2026-08-23T12:00:00Z","expires_at":None,"allowed_domains":["approved.example.invalid"],"external_fetch_allowed":True},"tier":"tier_2_team_locked","kind":"team_document","captured_at":"2026-08-23T12:00:00Z","effective_period":"2026","citation_location":"section-1","freshness_days":7}

    def test_owner_registers_authorized_source_without_fetching(self):
        status, response = handle_request(method="POST", path="/v1/sources/authorized", body=self._body(), headers=self.owner, service=self.service)
        self.assertEqual(status, 201)
        self.assertEqual(response["data"]["source"]["authorization_status"], "authorized")
        self.assertFalse(response["data"]["network_fetch_performed"])
        self.assertFalse(response["data"]["external_state_changed"])

    def test_non_owner_and_bad_authorization_are_rejected(self):
        status, _ = handle_request(method="POST", path="/v1/sources/authorized", body=self._body(), headers=self.analyst, service=self.service)
        self.assertEqual(status, 403)
        body = self._body()
        body["authorization"]["authorization_ref"] = "UNVERIFIED"
        status, response = handle_request(method="POST", path="/v1/sources/authorized", body=body, headers=self.owner, service=self.service)
        self.assertEqual(status, 422)
        self.assertEqual(response["status"], "invalid")


if __name__ == "__main__":
    unittest.main()

import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos import FootballIntelligenceService, JsonRepository, handle_request
from nfl_fidos.auth import issue_token


class ProviderAdapterApiTests(unittest.TestCase):
    def setUp(self):
        self.previous_secret = os.environ.get("NFL_FIDOS_AUTH_SECRET")
        self.secret = "provider-adapter-api-secret-0123456789"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = self.secret
        self.temp_directory = tempfile.TemporaryDirectory()
        self.service = FootballIntelligenceService(JsonRepository(Path(self.temp_directory.name) / "state.json"))
        self.analyst = {"Authorization": "Bearer " + issue_token(subject="ANALYST-1", role="analyst", organization_id="ORG-ADAPTER-API", secret=self.secret)}
        self.owner = {"Authorization": "Bearer " + issue_token(subject="OWNER-1", role="program_owner", organization_id="ORG-ADAPTER-API", secret=self.secret)}

    def tearDown(self):
        self.temp_directory.cleanup()
        if self.previous_secret is None:
            os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
        else:
            os.environ["NFL_FIDOS_AUTH_SECRET"] = self.previous_secret

    def test_submit_owner_validate_and_read(self):
        body = {"organization_id":"ORG-ADAPTER-API","adapter_id":"ADAPTER-API-001","provider":{"kind":"calendar","mode":"read_only","source_ref":"SOURCE-CALENDAR-001"},"capabilities":["practice_resources"],"credential_ref":"CREDENTIAL-CALENDAR-001","healthcheck_ref":"HEALTHCHECK-CALENDAR-001"}
        status, _ = handle_request(method="POST", path="/v1/integrations/provider-adapter", body=body, headers=self.analyst, service=self.service)
        self.assertEqual(status, 201)
        status, response = handle_request(method="POST", path="/v1/integrations/provider-adapter/approve", body={"organization_id":"ORG-ADAPTER-API","adapter_id":"ADAPTER-API-001","decision_ref":"DEC-ADAPTER-API-001"}, headers=self.owner, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual(response["data"]["status"], "validated")
        status, response = handle_request(method="GET", path="/v1/integrations/provider-adapter?organization_id=ORG-ADAPTER-API", headers=self.analyst, service=self.service)
        self.assertEqual(status, 200)
        self.assertEqual(len(response["data"]["registrations"]), 1)


if __name__ == "__main__":
    unittest.main()

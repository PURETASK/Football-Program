import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.repository import JsonRepository
from nfl_fidos.service import FootballIntelligenceService


class SourceApiTests(unittest.TestCase):
    def test_owner_registers_and_analyst_lists_authorized_sources(self):
        secret = "source-api-test-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        owner = {"Authorization": "Bearer " + issue_token(subject="OWNER-SOURCE", role="program_owner", organization_id="ORG-SOURCE-API", secret=secret)}
        analyst = {"Authorization": "Bearer " + issue_token(subject="ANALYST-SOURCE", role="analyst", organization_id="ORG-SOURCE-API", secret=secret)}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            body = {"organization_id":"ORG-SOURCE-API", "source_id":"SOURCE-API-001", "tier":"tier_1_authoritative", "kind":"official_rulebook", "uri":"https://rules.example.test/nfl", "captured_at":"2026-08-23", "effective_period":"2026-season", "citation_location":"rule 1", "allowed_domains":["rules.example.test"]}
            status, _ = handle_request(method="POST", path="/v1/sources", body=body, headers=owner, service=service)
            self.assertEqual(status, 201)
            status, payload = handle_request(method="GET", path="/v1/sources?organization_id=ORG-SOURCE-API", headers=analyst, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["sources"][0]["stale"], True)
            status, payload = handle_request(method="GET", path="/v1/operator/summary?organization_id=ORG-SOURCE-API", headers=analyst, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["role"], "analyst")
            service.repository.put("game_plans", "GAMEPLAN-INBOX-API", {"id":"GAMEPLAN-INBOX-API", "organization_id":"ORG-SOURCE-API", "status":"under_review", "source_refs":["SOURCE-API-001"]}, actor="OWNER-SOURCE", reason="fixture")
            status, payload = handle_request(method="GET", path="/v1/governance/inbox?organization_id=ORG-SOURCE-API", headers=owner, service=service)
            self.assertEqual(status, 200)
            self.assertEqual(payload["data"]["count"], 1)
            status, _ = handle_request(method="GET", path="/v1/governance/inbox?organization_id=ORG-SOURCE-API", headers=analyst, service=service)
            self.assertEqual(status, 403)
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)


if __name__ == "__main__":
    unittest.main()

import os
import unittest

from nfl_fidos.api import handle_request
from nfl_fidos.auth import authorize_principal, issue_token, verify_token


class AuthTenancyTests(unittest.TestCase):
    def test_signed_token_round_trip_and_expiry(self):
        token = issue_token(subject="coach-1", role="coach_staff", organization_id="ORG-1", secret="secret", ttl_seconds=60, now=100)
        principal = verify_token(token, secret="secret", now=120)
        self.assertEqual(principal.organization_id, "ORG-1")
        with self.assertRaises(ValueError):
            verify_token(token, secret="secret", now=161)

    def test_permission_and_tenant_scope_are_explicit(self):
        token = issue_token(subject="analyst-1", role="analyst", organization_id="ORG-1", secret="secret")
        principal = verify_token(token, secret="secret")
        self.assertTrue(authorize_principal(principal=principal, action="create_scouting_claim", organization_id="ORG-1")["allowed"])
        self.assertFalse(authorize_principal(principal=principal, action="create_scouting_claim", organization_id="ORG-2")["allowed"])
        self.assertFalse(authorize_principal(principal=principal, action="lock_artifact", organization_id="ORG-1")["allowed"])

    def test_workflow_api_requires_bearer_auth(self):
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)
        status, response = handle_request(method="POST", path="/v1/workflows/core-play", body={})
        self.assertEqual(status, 400)
        self.assertIn("organization_id", response["error"])
        status, response = handle_request(method="POST", path="/v1/workflows/core-play", body={"organization_id":"ORG-1", "play":{}, "role":"QB", "drill":{}, "actor":"x", "decision_ref":"DEC-1"})
        self.assertEqual(status, 401)

    def test_program_owner_read_all_applies_only_to_read_actions(self):
        token = issue_token(subject="owner-1", role="program_owner", organization_id="ORG-1", secret="secret")
        principal = verify_token(token, secret="secret")
        self.assertTrue(authorize_principal(principal=principal, action="read_film", organization_id="ORG-1")["allowed"])
        self.assertFalse(authorize_principal(principal=principal, action="draft_scouting", organization_id="ORG-1")["allowed"])


if __name__ == "__main__":
    unittest.main()

import sys
import unittest
from unittest.mock import patch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from nfl_fidos import handle_request, issue_token
from test_play_compiler import valid_play


class APITests(unittest.TestCase):
    def test_health_and_control_routes(self):
        status, response = handle_request(method="GET", path="/health")
        self.assertEqual(status, 200)
        self.assertEqual(response["status"], "ok")
        status, response = handle_request(method="GET", path="/v1/control")
        self.assertEqual(status, 200)
        self.assertEqual(response["data"]["work_package"], "STAGE-0A")

    def test_ontology_route_requires_query_and_resolves(self):
        secret = "s" * 32
        token = issue_token(subject="COACH-1", role="coach_staff", organization_id="ORG-1", secret=secret)
        headers = {"Authorization": "Bearer " + token}
        status, response = handle_request(method="GET", path="/v1/ontology/resolve?organization_id=ORG-1&term=gun")
        self.assertEqual(status, 401)
        with patch.dict("os.environ", {"NFL_FIDOS_AUTH_SECRET": secret}, clear=False):
            status, response = handle_request(method="GET", path="/v1/ontology/resolve")
            self.assertEqual(status, 400)
            status, response = handle_request(method="GET", path="/v1/ontology/resolve?organization_id=ORG-1&term=gun", headers=headers)
            self.assertEqual(status, 200)
            self.assertEqual(response["data"]["term_id"], "TERM-FORMATION-SHOTGUN")
            status, response = handle_request(method="GET", path="/v1/ontology/related?organization_id=ORG-1&term_id=TERM-CONCEPT-MESH&relationship_type=stresses", headers=headers)
            self.assertEqual(status, 200)
            self.assertEqual(response["data"]["relationships"][0]["term_id"], "TERM-COVERAGE-COVER-1")

    def test_program_owner_can_lock_team_alias_and_team_resolution_uses_it(self):
        secret = "s" * 32
        token = issue_token(subject="OWNER-1", role="program_owner", organization_id="ORG-1", secret=secret)
        headers = {"Authorization": "Bearer " + token}
        with patch.dict("os.environ", {"NFL_FIDOS_AUTH_SECRET": secret}, clear=False):
            status, response = handle_request(method="POST", path="/v1/ontology/team-aliases", headers=headers, body={"organization_id":"ORG-1", "team_id":"TEAM-A", "alias":"Blue Right", "term_id":"TERM-FORMATION-SHOTGUN", "reason":"team playbook terminology", "source_refs":["ORG-SOURCE-1"], "approval_ref":"APPROVAL-1"})
            self.assertEqual(status, 201)
            status, response = handle_request(method="GET", path="/v1/ontology/resolve?organization_id=ORG-1&team_id=TEAM-A&term=blue%20right", headers=headers)
            self.assertEqual(status, 200)
            self.assertEqual(response["data"]["status"], "resolved_team_alias")

    def test_compile_route_returns_contract_and_rejection_status(self):
        status, response = handle_request(method="POST", path="/v1/plays/compile", body=valid_play())
        self.assertEqual(status, 200)
        self.assertTrue(response["data"]["valid"])
        invalid = valid_play()
        invalid["assignments"] = []
        status, response = handle_request(method="POST", path="/v1/plays/compile", body=invalid)
        self.assertEqual(status, 422)
        self.assertEqual(response["status"], "invalid")

    def test_unknown_route_and_unsupported_method_are_explicit(self):
        status, response = handle_request(method="GET", path="/unknown")
        self.assertEqual(status, 404)
        status, response = handle_request(method="DELETE", path="/health")
        self.assertEqual(status, 405)


if __name__ == "__main__":
    unittest.main()

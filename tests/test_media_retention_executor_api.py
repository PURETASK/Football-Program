import tempfile
import unittest
import os
from pathlib import Path

from nfl_fidos import FootballIntelligenceService, JsonRepository
from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token


class MediaRetentionExecutorApiTests(unittest.TestCase):
    def test_owner_can_plan_but_execute_is_stage_gated(self):
        with tempfile.TemporaryDirectory() as directory:
            secret = "retention-execute-api-secret-012345678901234567890"
            os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            owner = {"Authorization": "Bearer " + issue_token(subject="OWNER", role="program_owner", organization_id="ORG-RETENTION-API", secret=secret)}
            root = Path(directory) / "managed"
            root.mkdir()
            response = handle_request(method="POST", path="/v1/media/retention-execute", body={"organization_id":"ORG-RETENTION-API", "managed_root":str(root), "environment":"production", "execute":True, "approval_ref":"APPROVAL-1"}, headers=owner, service=service)
            self.assertEqual(response[0], 403)
            self.assertIn("Stage 0", response[1]["error"])
            os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)

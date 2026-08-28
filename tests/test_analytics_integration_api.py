import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.repository import JsonRepository
from nfl_fidos.service import FootballIntelligenceService


class AnalyticsIntegrationApiTests(unittest.TestCase):
    def test_analyst_can_submit_scoped_metric_batch(self):
        secret = "analytics-integration-api-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        headers = {"Authorization":"Bearer "+issue_token(subject="ANALYST-INTEGRATION-API", role="analyst", organization_id="ORG-ANALYTICS-API", secret=secret)}
        definition = {"id":"METRIC-DEF-API-RATE", "name":"API rate", "unit":"rate", "definition":"successes", "required_data":["play_id"], "formula":"numerator / denominator", "context_dimensions":["situation"], "caveats":["sample"], "validation_method":"review", "consumers":["coach_staff"]}
        body = {"organization_id":"ORG-ANALYTICS-API", "provider":{"kind":"approved_export", "mode":"read_only", "source_ref":"PROVIDER-ANALYTICS-001"}, "batch_id":"ANALYTICS-BATCH-API-001", "records":[{"definition":definition, "numerator":5, "denominator":10, "context":{"situation":"red_zone"}, "observation_ids":["PLAY-API-001"]}], "source_manifest":{"kind":"approved_export", "ref":"PROVIDER-ANALYTICS-001"}}
        with tempfile.TemporaryDirectory() as directory:
            service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
            status, payload = handle_request(method="POST", path="/v1/analytics/batches", headers=headers, body=body, service=service)
            self.assertEqual(status, 201)
            self.assertEqual(payload["data"]["accepted_count"], 1)
            self.assertEqual(len(service.repository.list("metric_observations")), 1)
        os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)


if __name__ == "__main__":
    unittest.main()

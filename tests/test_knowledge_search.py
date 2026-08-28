import os
import tempfile
import unittest
from pathlib import Path

from nfl_fidos.api import handle_request
from nfl_fidos.auth import issue_token
from nfl_fidos.knowledge_search import KnowledgeRetrievalService
from nfl_fidos.repository import JsonRepository
from nfl_fidos.service import FootballIntelligenceService
from nfl_fidos.sqlite_repository import SqliteRepository
from nfl_fidos.tenant_repository import TenantRepository


class KnowledgeSearchTests(unittest.TestCase):
    def test_json_fallback_is_organization_scoped_and_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            base = JsonRepository(Path(directory) / "state.json")
            tenant = TenantRepository(base, organization_id="ORG-KNOWLEDGE", actor="ANALYST")
            tenant.put("knowledge_items", "KNOWLEDGE-001", {"id":"KNOWLEDGE-001", "organization_id":"ORG-KNOWLEDGE", "normalized_claim":"two high coverage rule", "classification":"rule", "state":"current", "source_id":"SOURCE-1"}, actor="ANALYST", reason="test_seed")
            results = KnowledgeRetrievalService(tenant).search(query="two high", limit=1)
            self.assertEqual([item["record"]["id"] for item in results], ["KNOWLEDGE-001"])
            with self.assertRaises(ValueError):
                KnowledgeRetrievalService(tenant).search(limit=501)

    def test_sqlite_fts_indexes_and_retrieves_provenance_records(self):
        with tempfile.TemporaryDirectory() as directory:
            base = SqliteRepository(Path(directory) / "state.sqlite")
            tenant = TenantRepository(base, organization_id="ORG-KNOWLEDGE", actor="ANALYST")
            tenant.put("knowledge_claims", "CLAIM-001", {"id":"CLAIM-001", "organization_id":"ORG-KNOWLEDGE", "claim":"red zone tendency", "classification":"observed_tendency", "state":"current", "source_refs":["CLIP-1"], "uncertainty":["small sample"]}, actor="ANALYST", reason="test_seed")
            results = KnowledgeRetrievalService(tenant).search(query="red zone")
            self.assertEqual(results[0]["record"]["source_refs"], ["CLIP-1"])
            base.close()

    def test_api_search_requires_organization_scope(self):
        secret = "knowledge-search-secret-012345678901234567890"
        os.environ["NFL_FIDOS_AUTH_SECRET"] = secret
        try:
            with tempfile.TemporaryDirectory() as directory:
                service = FootballIntelligenceService(JsonRepository(Path(directory) / "state.json"))
                service.repository.put("knowledge_items", "KNOWLEDGE-API", {"id":"KNOWLEDGE-API", "organization_id":"ORG-KNOWLEDGE-API", "normalized_claim":"NFL rule evidence", "classification":"rule", "state":"current"}, actor="OWNER", reason="test_seed")
                analyst = {"Authorization":"Bearer " + issue_token(subject="ANALYST-KNOWLEDGE", role="analyst", organization_id="ORG-KNOWLEDGE-API", secret=secret)}
                other = {"Authorization":"Bearer " + issue_token(subject="ANALYST-OTHER", role="analyst", organization_id="ORG-OTHER", secret=secret)}
                status, payload = handle_request(method="GET", path="/v1/knowledge/search?organization_id=ORG-KNOWLEDGE-API&query=NFL+rule", headers=analyst, service=service)
                self.assertEqual(status, 200)
                self.assertEqual(payload["data"]["count"], 1)
                self.assertEqual(handle_request(method="GET", path="/v1/knowledge/search?organization_id=ORG-KNOWLEDGE-API", headers=other, service=service)[0], 403)
        finally:
            os.environ.pop("NFL_FIDOS_AUTH_SECRET", None)


if __name__ == "__main__":
    unittest.main()

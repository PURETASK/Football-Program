import copy
import unittest

from nfl_fidos.source_authorization import load_source_authorization, validate_source_authorization


class SourceAuthorizationTests(unittest.TestCase):
    def test_authorized_template_is_ready_without_network_or_state_change(self):
        result = validate_source_authorization(authorization=load_source_authorization("operations/source-authorization-template.json"), environment="validation")
        self.assertEqual(result["status"], "authorized")
        self.assertFalse(result["network_fetch_performed"])
        self.assertFalse(result["external_state_changed"])

    def test_missing_license_or_domain_evidence_blocks(self):
        authorization = load_source_authorization("operations/source-authorization-template.json")
        authorization["authorization_ref"] = "UNVERIFIED"
        authorization["allowed_domains"] = ["other.example.invalid"]
        result = validate_source_authorization(authorization=authorization, environment="validation")
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("authorization_ref" in issue for issue in result["issues"]))
        self.assertTrue(any("authorized domain" in issue for issue in result["issues"]))

    def test_production_official_source_requires_explicit_approval(self):
        authorization = load_source_authorization("operations/source-authorization-template.json")
        authorization["license_class"] = "official_public"
        authorization["authorization_ref"] = "DEC-SOURCE-EXAMPLE-001"
        result = validate_source_authorization(authorization=authorization, environment="production")
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("production official" in issue for issue in result["issues"]))


if __name__ == "__main__":
    unittest.main()

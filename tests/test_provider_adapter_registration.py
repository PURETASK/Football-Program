import unittest

from nfl_fidos.provider_adapter_registration import approve_provider_adapter_registration, build_provider_adapter_registration


class ProviderAdapterRegistrationTests(unittest.TestCase):
    def test_valid_registration_and_owner_certification_remain_non_external(self):
        registration = build_provider_adapter_registration(adapter_id="ADAPTER-001", organization_id="ORG-ADAPTER", provider={"kind":"analytics","mode":"read_only","source_ref":"PROVIDER-001"}, capabilities=["analytics"], credential_ref="SECRET-ANALYTICS-001", healthcheck_ref="HEALTHCHECK-001")
        self.assertEqual(registration["status"], "under_review")
        approved = approve_provider_adapter_registration(registration=registration, approver="OWNER-1", approver_role="program_owner", decision_ref="DEC-ADAPTER-001")
        self.assertEqual(approved["status"], "validated")
        self.assertFalse(approved["external_provider_called"])
        self.assertFalse(approved["external_registration_performed"])
        self.assertFalse(approved["production_implementation_allowed"])

    def test_secret_like_credential_value_is_rejected(self):
        registration = build_provider_adapter_registration(adapter_id="ADAPTER-002", organization_id="ORG-ADAPTER", provider={"kind":"media","mode":"write","source_ref":"PROVIDER-002"}, capabilities=["media"], credential_ref="token-value-should-not-appear", healthcheck_ref="HEALTHCHECK-002")
        self.assertEqual(registration["status"], "rejected")
        self.assertTrue(any(issue["code"] == "ADAPTER-CREDENTIAL" for issue in registration["issues"]))

    def test_malformed_registration_payload_fails_closed_without_type_error(self):
        registration = build_provider_adapter_registration(adapter_id="ADAPTER-003", organization_id="ORG-ADAPTER", provider=None, capabilities="analytics", credential_ref=None, healthcheck_ref=42)
        self.assertEqual(registration["status"], "rejected")
        codes = {issue["code"] for issue in registration["issues"]}
        self.assertTrue({"ADAPTER-PROVIDER", "ADAPTER-CAPABILITY-SHAPE", "ADAPTER-CREDENTIAL-SHAPE", "ADAPTER-HEALTHCHECK-SHAPE"}.issubset(codes))


if __name__ == "__main__":
    unittest.main()

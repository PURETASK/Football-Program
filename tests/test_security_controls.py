import unittest

from src.nfl_fidos.security_controls import SlidingWindowRateLimiter, redact_sensitive, sign_payload, verify_payload_signature


class SecurityControlsTests(unittest.TestCase):
    def test_redaction_removes_credentials_from_nested_evidence(self):
        payload = {"actor": "coach", "authorization": "Bearer secret", "nested": {"api_key": "key", "safe": "visible"}, "items": [{"password": "pw"}]}
        redacted = redact_sensitive(payload)
        self.assertEqual(redacted["authorization"], "[REDACTED]")
        self.assertEqual(redacted["nested"]["api_key"], "[REDACTED]")
        self.assertEqual(redacted["nested"]["safe"], "visible")
        self.assertEqual(redacted["items"][0]["password"], "[REDACTED]")

    def test_signed_artifact_payload_detects_tampering(self):
        payload = {"artifact_id": "ART-1", "organization_id": "ORG-1", "sha256": "a" * 64}
        signature = sign_payload(payload, secret="security-test-secret-0123456789")
        self.assertTrue(verify_payload_signature(payload, signature=signature, secret="security-test-secret-0123456789"))
        payload["organization_id"] = "ORG-2"
        self.assertFalse(verify_payload_signature(payload, signature=signature, secret="security-test-secret-0123456789"))

    def test_sliding_window_rate_limiter_returns_retry_metadata(self):
        limiter = SlidingWindowRateLimiter(limit=2, window_seconds=10)
        self.assertTrue(limiter.check("ORG-1:coach", now=100)["allowed"])
        self.assertTrue(limiter.check("ORG-1:coach", now=101)["allowed"])
        blocked = limiter.check("ORG-1:coach", now=102)
        self.assertFalse(blocked["allowed"])
        self.assertGreaterEqual(blocked["retry_after_seconds"], 1)
        self.assertTrue(limiter.check("ORG-1:analyst", now=102)["allowed"])
        self.assertTrue(limiter.check("ORG-1:coach", now=111)["allowed"])


if __name__ == "__main__":
    unittest.main()

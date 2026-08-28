import unittest

from scripts.secret_manager_mount_rehearsal import run_rehearsal


class SecretManagerMountRehearsalTests(unittest.TestCase):
    def test_mount_rehearsal_is_value_redacted_and_fail_closed(self):
        result = run_rehearsal()
        self.assertEqual(result["status"], "passed")
        self.assertTrue(result["checks"]["value_redacted"])
        self.assertTrue(result["checks"]["missing_mount_fails_closed"])
        self.assertFalse(result["external_provider_called"])


if __name__ == "__main__":
    unittest.main()

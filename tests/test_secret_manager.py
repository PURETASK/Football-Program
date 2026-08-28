import tempfile
import unittest
from pathlib import Path

from nfl_fidos.config import resolve_auth_secret
from nfl_fidos.secret_manager import inspect_secret_manager_mount, resolve_secret_manager_mount
from nfl_fidos.secret_source import inspect_secret_source


class SecretManagerTests(unittest.TestCase):
    def test_valid_manager_mount_resolves_without_exposing_value(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "secret"
            value = "x" * 40
            path.write_text(value, encoding="utf-8")
            environ = {"NFL_FIDOS_ENV":"production", "NFL_FIDOS_SECRET_PROVIDER":"approved_secret_manager_mount", "NFL_FIDOS_SECRET_MANAGER_NAME":"nfl-fidos-auth", "NFL_FIDOS_SECRET_VERSION":"v1", "NFL_FIDOS_SECRET_MANAGER_FILE":str(path)}
            report = inspect_secret_manager_mount(environ=environ, environment="production")
            self.assertEqual(report["status"], "valid")
            self.assertFalse(report["value_exposed"])
            self.assertNotIn(value, str(report))
            self.assertEqual(resolve_secret_manager_mount(environ=environ), value)
            self.assertEqual(resolve_auth_secret(environ=environ), value)
            self.assertEqual(inspect_secret_source(environ=environ, environment="production", require_external_source=True)["source_type"], "approved_secret_manager_mount")

    def test_missing_metadata_or_mount_fails_closed(self):
        environ = {"NFL_FIDOS_ENV":"production", "NFL_FIDOS_SECRET_PROVIDER":"approved_secret_manager_mount", "NFL_FIDOS_SECRET_MANAGER_NAME":"nfl-fidos-auth", "NFL_FIDOS_SECRET_VERSION":"v1", "NFL_FIDOS_SECRET_MANAGER_FILE":"C:\\missing\\secret", "NFL_FIDOS_AUTH_SECRET":"x" * 64}
        report = inspect_secret_source(environ=environ, environment="production", require_external_source=True)
        self.assertEqual(report["status"], "invalid")
        with self.assertRaises(ValueError):
            resolve_auth_secret(environ=environ)


if __name__ == "__main__":
    unittest.main()

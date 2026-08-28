import unittest

from nfl_fidos.demo_data import default_database_path
from scripts.play_designer_http_rehearsal import run_rehearsal


class PlayDesignerHttpRehearsalTests(unittest.TestCase):
    def test_ephemeral_authenticated_rehearsal_reads_seeded_play_designer_contracts(self):
        database = default_database_path()
        self.assertTrue(database.is_file(), "Run scripts/seed_demo_data.py before the synthetic rehearsal test")
        report = run_rehearsal(database=database)
        self.assertEqual(report["status"], "passed")
        self.assertTrue(report["synthetic"])
        self.assertEqual(len(report["checks"]), 5)
        self.assertTrue(all(check["passed"] for check in report["checks"]))
        self.assertTrue(all(not value for value in report["safety"].values()))


if __name__ == "__main__":
    unittest.main()

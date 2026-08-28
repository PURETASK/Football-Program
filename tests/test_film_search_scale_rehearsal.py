import unittest

from scripts.film_search_scale_rehearsal import run_rehearsal


class FilmSearchScaleRehearsalTests(unittest.TestCase):
    def test_bounded_search_scale_preserves_persistence_and_tenancy(self):
        result = run_rehearsal(observations_per_tenant=8)
        self.assertEqual(result["status"], "passed")
        self.assertTrue(result["checks"]["fts_available"])
        self.assertTrue(result["checks"]["cross_tenant_isolation"])
        self.assertTrue(result["checks"]["persistence"])


if __name__ == "__main__":
    unittest.main()

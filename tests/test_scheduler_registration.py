import unittest

from nfl_fidos.scheduler_registration import load_scheduler_registration, validate_scheduler_registration


class SchedulerRegistrationTests(unittest.TestCase):
    def test_validation_registration_is_ready_without_external_write(self):
        result = validate_scheduler_registration(
            registration=load_scheduler_registration(),
            environ={"NFL_FIDOS_SCHEDULER_PROVIDER": "provider_neutral", "NFL_FIDOS_SCHEDULER_REGISTRATION_REF": "SCHEDULER-REG-001"},
            environment="validation",
        )
        self.assertEqual(result["status"], "ready")
        self.assertFalse(result["external_registration_performed"])
        self.assertFalse(result["external_state_changed"])
        self.assertTrue(result["dry_run_default"])

    def test_production_and_provider_boundaries_fail_closed(self):
        result = validate_scheduler_registration(
            registration=load_scheduler_registration(),
            environ={"NFL_FIDOS_SCHEDULER_PROVIDER": "vendor_unknown"},
            environment="production",
        )
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("provider-neutral" in issue for issue in result["issues"]))
        self.assertTrue(any("SCHEDULER-REG-" in issue for issue in result["issues"]))

    def test_invalid_job_and_bound_are_rejected(self):
        registration = load_scheduler_registration()
        registration["jobs"][0]["operation"] = "unknown"
        registration["bounds"]["max_sources"] = 0
        result = validate_scheduler_registration(registration=registration, environment="validation")
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("unsupported scheduler operation" in issue for issue in result["issues"]))
        self.assertTrue(any("max_sources" in issue for issue in result["issues"]))


if __name__ == "__main__":
    unittest.main()

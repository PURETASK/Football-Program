# Operational readiness rehearsal

Run `python scripts/operational_rehearsal.py` from the repository root. The
rehearsal creates a temporary SQLite database, applies the current migration,
backs it up and restores it, runs the validation-environment readiness checks,
plans bounded scheduled operations, and confirms that an attempted production
execution is blocked by the Stage 0 control gate.

The rehearsal must report `status: passed`, `external_state_changed: false`,
and `production_guard_status: blocked`. It does not provision infrastructure,
send data to external services, enable production, or alter the control
manifest.

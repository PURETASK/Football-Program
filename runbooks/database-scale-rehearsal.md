# NFL FIDOS Database Scale Rehearsal

Run `python scripts/database_scale_rehearsal.py --records-per-tenant 100` to create a temporary SQLite database, apply migrations, write synthetic records for two organizations, read each tenant scope, and verify append-only audit history.

The rehearsal is bounded to 10,000 records per tenant, uses a temporary workspace, and reports `external_state_changed: false`. Timing output is diagnostic rather than a production service-level objective; production capacity targets require deployment-environment measurement.

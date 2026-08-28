# NFL FIDOS Database Backup Scheduling

The backup scheduler creates a bounded plan, verifies the source SQLite database, and optionally creates one atomically named backup. Planning is the default. Retention planning is evidence-only; it never deletes files. Any production execution remains blocked while `control/manifest.json` has `production_implementation_allowed: false`.

## Validation procedure

1. Run `python scripts/schedule_backup.py .runtime/nfl_fidos.sqlite3 .runtime/backups --actor OWNER`.
2. Confirm the plan reports source integrity, freshness, due status, and retention candidates.
3. Execute only in an approved non-production rehearsal with `--execute`.
4. Confirm the result reports `status: completed`, `content_match: true`, and a valid destination verification.
5. Preserve the JSON result with the operational evidence package. Do not delete retention candidates until a separate owner-approved retention operation exists.

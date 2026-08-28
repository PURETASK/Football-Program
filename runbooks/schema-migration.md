# Schema migration

1. Run `python scripts/migrate_sqlite.py DATABASE --dry-run`.
2. Create a named snapshot before applying the migration.
3. Apply the migration and run tests, evals, and control validation.
4. Inspect revision counts, organization keys, and append-only audit history.
5. If a gate fails, stop promotion and run `python scripts/migrate_sqlite.py DATABASE --rollback SNAPSHOT`.

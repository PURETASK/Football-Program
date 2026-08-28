# Database backup and restore

1. Verify the source with `python scripts/backup_sqlite.py verify DATABASE`.
2. Create a verified backup with `python scripts/backup_sqlite.py backup DATABASE BACKUP`.
   The result includes logical database source/destination SHA-256 fingerprints derived from the SQLite dump; `content_match` must be true.
3. Run the regression suite, eval suite, and control-plane validator before promotion.
4. Use the retention planner to identify candidates; deletion requires an explicit owner-approved operation.
5. The retention scan persists review evidence but never deletes media; any deletion workflow must be separately approved and implemented.
5. Restore only from a verified backup, then rerun integrity, migration, regression, and tenancy checks.

Run the bounded temporary restore drill with `python scripts/validate_database_operations.py`. It creates and removes only a temporary test database and does not touch the configured application database.

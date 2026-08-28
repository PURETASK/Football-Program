# Release Preflight

Run `python scripts/release_preflight.py --environment validation` to compose release-artifact validation, deployment-contract and secret-source preflight, operational readiness, and the independent evaluation suite into one evidence report.

`ready_for_validation` means the evidence is coherent for a validation environment; it is not permission to deploy production. The report always preserves `activation_performed: false`, `production_implementation_allowed: false`, and `external_state_changed: false` while Stage 0 approval is open. Missing or unmigrated databases, missing external secret sources, failed evaluations, or invalid contracts produce explicit blockers.

## Validation rehearsal

To exercise the successful validation path without touching a persistent or production database, create a temporary migrated SQLite database and pass it to the preflight command:

```powershell
$db = Join-Path ([System.IO.Path]::GetTempPath()) ("nfl-fidos-validation-$([guid]::NewGuid()).sqlite3")
try {
  python scripts/migrate_sqlite.py $db
  $env:NFL_FIDOS_ENV = "validation"
  $env:NFL_FIDOS_AUTH_SECRET = "validation-preflight-secret-1234567890"
  python scripts/release_preflight.py --environment validation --database $db
} finally {
  if (Test-Path -LiteralPath $db) { Remove-Item -LiteralPath $db -Force }
}
```

Expected successful evidence is `status: ready_for_validation`, while `activation_performed`, `production_implementation_allowed`, and `external_state_changed` remain `false`. Running without a migrated database is expected to return `status: blocked`.

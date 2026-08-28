# Synthetic demo data

The demo seed is a local-only showcase tenant that exercises the real NFL FIDOS repository, API workspaces, Play Designer, teaching views, collaboration records, exports, and governance surfaces. It is not a real team, roster, opponent, source, approval, or production release.

## Seed the default local database

From the project root:

```powershell
$env:PYTHONPATH = (Resolve-Path '.\\src').Path
python scripts/seed_demo_data.py
```

The default target is `NFL_FIDOS_DATABASE` when set, otherwise `.runtime/nfl_fidos.sqlite3`. The seed is idempotent: rerunning it reports `already_seeded` instead of creating duplicates. To intentionally recreate the exact demo seed, use the explicit confirmation:

```powershell
$env:PYTHONPATH = (Resolve-Path '.\\src').Path
python scripts/seed_demo_data.py --replace --confirm RESEED-SYNTHETIC-DEMO-DATA
```

Use `--no-media` when FFmpeg is unavailable. Without that option, the script attempts to create a tiny local synthetic MP4 under `.runtime/nfl-fidos-demo-media/`. No network source or provider is called.

To create a durable Stage 0 owner-review artifact containing the synthetic walkthrough map, population-readiness result, and explicit approval boundary:

```powershell
$env:PYTHONPATH = (Resolve-Path '.\\src').Path
python scripts/stage0_rehearsal.py --no-media --output .\\runtime\\stage0-owner-review.json
```

This report is review evidence only. It does not record owner approval,
advance the stage, activate production, or contact an external provider.

## Open the authenticated dashboard

Set a local secret in the same PowerShell session used to run the server:

```powershell
$env:PYTHONPATH = (Resolve-Path '.\\src').Path
$env:NFL_FIDOS_AUTH_SECRET = 'local-demo-secret-change-me-32-characters'
$env:NFL_FIDOS_DATABASE = '.runtime/nfl_fidos.sqlite3'
python -m nfl_fidos.server
```

If the package is not installed in the current environment, run the project’s normal editable install first or use the existing local server entry point. Issue a demo coach token in a second terminal:

```powershell
$env:PYTHONPATH = (Resolve-Path '.\\src').Path
$env:NFL_FIDOS_AUTH_SECRET = 'local-demo-secret-change-me-32-characters'
python scripts/issue_demo_token.py --role coach_staff
```

Paste these values into the dashboard’s Film Room authentication fields:

- Organization: `ORG-DEMO-FIDOS-001`
- Token: the token printed by `issue_demo_token.py`

Useful demo entry points include `PD-DEMO-OFF-DAGGER` (published offense), `PD-DEMO-DEF-COVER3` (review-pending defense), `PD-DEMO-OFF-DAGGER-COUNTER` (branch), `PLAYER-DEMO-QB-1`, `OPP-DEMO-LIONS`, and `WEEK-1`.

For a repeatable authenticated Play Designer HTTP rehearsal that is isolated
from any already-running local server, use:

```powershell
$env:PYTHONPATH = (Resolve-Path '.\\src').Path
python scripts/play_designer_http_rehearsal.py
```

This starts an ephemeral local server with the documented synthetic secret,
reads the seeded workspace, versions, legality report, QB player view, and
release-bundle integrity record, then shuts the server down. It is read-only
and reports explicit non-production safety flags. A 503 from an already-running
server usually indicates that process was started with a different
`NFL_FIDOS_AUTH_SECRET`; the isolated rehearsal avoids changing or terminating
that process.

## Inspect without changing anything

```powershell
$env:PYTHONPATH = (Resolve-Path '.\\src').Path
python scripts/seed_demo_data.py --dry-run
python scripts/delete_demo_data.py --dry-run
```

## Delete the demo seed

Stop the local server first so no request is writing while cleanup runs. Then execute:

```powershell
$env:PYTHONPATH = (Resolve-Path '.\\src').Path
python scripts/delete_demo_data.py --confirm DELETE-SYNTHETIC-DEMO-DATA
```

Cleanup is fail-closed. It refuses production mode, requires the exact confirmation phrase, is locked to `ORG-DEMO-FIDOS-001`, and deletes only records carrying both `synthetic_demo: true` and the requested `demo_seed_id`. It also removes only the seed-named MP4 and owned marker file under the demo media directory; unrelated records and files are preserved. The script reports deleted record/event counts and remaining file handling.

If a custom seed id was used, pass the same `--seed-id DEMO-SEED-...` to the cleanup command. Never point this command at a production data mount.

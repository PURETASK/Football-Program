# Stage 0 synthetic rehearsal

This is a safe way to prepare and inspect the Stage 0 workflow before real
organization data and owner approval exist. It creates a clearly marked
synthetic organization in a local repository and produces one combined report
containing:

- a synthetic roster, staff, playbook, film, practice, scouting, analytics,
  game-plan, learning, collaboration, and delivery dataset;
- the persisted organization operating-set components and population
  readiness evidence; and
- the current Stage 0 owner-review packet, including its real blockers and
  acceptance evidence.

The rehearsal does **not** record owner approval, advance the stage, activate
production, call an external provider, or change an external system. Synthetic
records are marked with `synthetic_demo`, `demo_seed_id`, and
`SAFE-TO-DELETE-SYNTHETIC-DEMO`.

## Run a rehearsal

From the repository root:

```powershell
python scripts/stage0_rehearsal.py --database .runtime/stage0-demo.sqlite3
```

For a fast run that skips optional FFmpeg media generation:

```powershell
python scripts/stage0_rehearsal.py --database .runtime/stage0-demo.sqlite3 --no-media
```

To verify the seeded database through the running HTTP application, use the
bounded runtime smoke. It seeds only the synthetic tenant, starts an ephemeral
local server, checks the React shell/assets and an authenticated Playbook
workspace, then shuts the server down:

```powershell
python scripts/stage0_runtime_smoke.py --database .runtime/stage0-demo.sqlite3
```

The smoke is local-only and its report keeps production, stage advancement, and
external-state flags disabled.

The command prints JSON. The important safety fields must remain:

```json
{
  "owner_approval_recorded": false,
  "stage_advance_authorized": false,
  "production_implementation_allowed": false,
  "activation_performed": false,
  "external_state_changed": false
}
```

Use the returned demo entry points to open the local dashboard, Play Designer,
defensive design, player learning record, opponent profile, and weekly plan.
The exact synthetic identifiers are also returned by the existing seed command.

## Inspect without changing anything

```powershell
python scripts/stage0_rehearsal.py --database .runtime/stage0-demo.sqlite3 --dry-run
```

## Delete the synthetic data

The cleanup command is fail-closed and deletes only the exact synthetic
organization/seed. It preserves unrelated organizations and records.

First inspect the deletion scope:

```powershell
python scripts/delete_demo_data.py --database .runtime/stage0-demo.sqlite3 --dry-run
```

Then delete it explicitly:

```powershell
python scripts/delete_demo_data.py `
  --database .runtime/stage0-demo.sqlite3 `
  --confirm DELETE-SYNTHETIC-DEMO-DATA
```

The cleanup also removes the generated media only when its ownership marker
matches the exact synthetic organization and seed. It refuses to run when
`NFL_FIDOS_ENV=production` or against the protected production data mount.

## What still requires a real Stage 0 decision

The rehearsal is evidence preparation, not the decision itself. Stage 0 still
requires the program owner to review the Markdown/DOCX-derived registry, gap
audit, and exit gate, then submit real rationale and evidence through the
owner-only approval path. Do not replace the approval payload placeholders with
synthetic values merely to make the gate pass.

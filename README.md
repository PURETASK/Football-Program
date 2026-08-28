# NFL Football Intelligence & Development OS

NFL FIDOS is an organization-scoped football intelligence, playbook,
development, practice, scouting, game-plan, collaboration, and governance
system. The Python API and football-domain services remain authoritative; the
React + TypeScript application is the current user-facing workspace.

This repository implements the controlled master plan in
`governance/master-plan/NFL_Football_Intelligence_OS_Master_Codex_Plan_v1.0.md`
and its DOCX companion. The project is NFL-scoped and intentionally keeps
owner approval, production activation, live-source authorization, and pilot
evidence behind explicit gates.

## Quick start

Requirements:

- Python 3.11 or newer
- Node.js 24 or newer
- PowerShell on Windows or an equivalent shell

Install dependencies:

```powershell
python -m pip install -e .
npm.cmd ci --prefix frontend
```

Run local validation:

```powershell
$env:PYTHONPATH = (Resolve-Path '.\\src').Path
python -m unittest discover -s tests -p 'test*.py' -q
npm.cmd test --prefix frontend
npm.cmd run typecheck --prefix frontend
npm.cmd run build --prefix frontend
```

## Run the local application

```powershell
$env:PYTHONPATH = (Resolve-Path '.\\src').Path
$env:NFL_FIDOS_AUTH_SECRET = 'local-demo-secret-change-me-32-characters'
$env:NFL_FIDOS_DATABASE = '.runtime/nfl_fidos.sqlite3'
python -m nfl_fidos.server
```

The server is available at `http://127.0.0.1:8080`. The React application is
served under `/app`; the legacy operator dashboard remains available at
`/operator-dashboard` during the incremental migration.

Important routes include:

- `/app` — Today command center
- `/app/playbook` — visual Playbook library
- `/app/playbook/designer/new` — new Play Designer workspace
- `/app/playbook/designer/:id` — existing Play Designer design
- `/app/inbox` — Unified Operations Inbox
- `/app/film` — Film Intelligence Studio
- `/app/practice` — Practice and Install Builder
- `/app/scouting` — Scouting Tendency Explorer
- `/app/game-plan` — Game Plan Release Room
- `/app/player` — Player Learning Hub
- `/app/roster` — Roster and Personnel
- `/app/collaboration` — collaboration and notifications
- `/app/admin` — organization, sources, Stage 0, and pilot governance
- `/app/reviews` — governed review queue
- `/app/stage-25` — specification acceptance contract

## Synthetic Stage 0 environment

The repository includes a marked local-only synthetic organization:

```text
Organization: ORG-DEMO-FIDOS-001
Seed: DEMO-SEED-2026-08-24
Synthetic: true
Production activation: false
Owner approval: false
Stage advancement: false
```

Seed it with:

```powershell
$env:PYTHONPATH = (Resolve-Path '.\\src').Path
python scripts/seed_demo_data.py
```

Generate the Stage 0 owner-review rehearsal packet:

```powershell
python scripts/stage0_rehearsal.py `
  --no-media `
  --output .\\runtime\\stage0-owner-review.json
```

Issue a synthetic coach token in a second terminal:

```powershell
$env:PYTHONPATH = (Resolve-Path '.\\src').Path
$env:NFL_FIDOS_AUTH_SECRET = 'local-demo-secret-change-me-32-characters'
python scripts/issue_demo_token.py --role coach_staff
```

Use organization `ORG-DEMO-FIDOS-001` and the printed token in the app. Useful
synthetic records include `PD-DEMO-OFF-DAGGER`, `PD-DEMO-DEF-COVER3`,
`PD-DEMO-OFF-DAGGER-COUNTER`, `PLAYER-DEMO-QB-1`, `OPP-DEMO-LIONS`, and
`WEEK-1`.

For an isolated, read-only authenticated Play Designer rehearsal:

```powershell
python scripts/play_designer_http_rehearsal.py
```

See [runbooks/demo-seed-data.md](runbooks/demo-seed-data.md) for the complete
demo workflow. Delete only the marked synthetic seed after stopping the server:

```powershell
python scripts/delete_demo_data.py `
  --confirm DELETE-SYNTHETIC-DEMO-DATA
```

The cleanup is fail-closed and preserves unrelated records and files.

## Play Designer

The Play Designer is an integrated application workspace, not a disconnected
drawing utility. It uses the canonical versioned design model for the diagram,
assignments, animation, teaching views, legality, collaboration, publishing,
and exports.

Current capabilities include:

- Searchable organization-aware asset registry
- Formation, route, motion, run, protection, block, front, coverage, pressure,
  stunt, rotation, check, and teaching assets
- System and organization concept templates
- Pointer and keyboard authoring
- Route/path handles, landmarks, timing, layers, locking, snapping, grouping,
  copy/paste, undo/redo, and mirroring
- Offensive and defensive assignment editing
- Defensive fronts, coverage shells, exchanges, rotations, and gap ownership
- Timeline playback, synchronized events, reads, block/rush exchanges, and
  teaching narration
- NFL, NCAA, high-school, youth, and flag legality profiles
- Explainable validation and owner-review override workflow
- Presence, comments, replies, resolution, branching, diffs, guarded merges,
  immutable release bundles, and rollback
- Coordinator, position-group, and player teaching views
- PDF, SVG, PNG, HTML, JSON, CSV, call-sheet, wristband, and install-sheet
  export contracts
- Offline draft recovery, encrypted local caches, retry handling, and conflict
  visualization

Read the detailed blueprint at
[PLAY_DESIGNER_BUILD_GUIDE.md](PLAY_DESIGNER_BUILD_GUIDE.md) and the user
tutorial at [runbooks/play-designer-tutorial.md](runbooks/play-designer-tutorial.md).

## Evidence and governance

Run the project audit and persist its checkpoint:

```powershell
$env:PYTHONPATH = (Resolve-Path '.\\src').Path
python scripts/project_audit.py `
  --output .\\runtime\\project-audit-latest.json
```

The report records source hashes, traceability, evaluation status, blockers,
Stage 0 state, and production authorization. It preserves
`completion_claimed: false` until every required gate is genuinely complete.

Other validators:

```powershell
python scripts/validate_control_plane.py
python scripts/validate_traceability.py
python scripts/audit_feature_parity.py
python scripts/validate_browser_evidence.py
python scripts/validate_deployment_contract.py
```

GitHub Actions runs the core checks and uploads the persisted audit as the
`master-plan-audit-evidence` artifact. See
[runbooks/project-audit.md](runbooks/project-audit.md) and
[runbooks/frontend-migration.md](runbooks/frontend-migration.md).

## Safety and approval boundaries

Local tests, synthetic records, deterministic evaluations, and a successful
build are implementation evidence. They are not:

- Program-owner approval
- Authorization to advance Stage 0
- Production deployment approval
- Authorization to retrieve live sources
- Proof of real organization doctrine or roster data
- Proof of moderated pilot acceptance

The control plane remains fail-closed. Real owner approval, organization data,
external provider configuration, production secrets, monitoring registration,
deployment validation, and pilot evidence must come through governed workflows.

## Repository layout

```text
src/nfl_fidos/       Python API and football-domain services
frontend/            React + TypeScript application
playbook/            Asset registry, templates, and play families
rules/               Rule profiles and legality references
control/             Stage gates, traceability, evidence, and governance
contracts/           JSON contracts and schemas
scripts/             Rehearsals, validators, seed, cleanup, and audit tools
runbooks/            Operational and feature-use instructions
tests/               Python regression and integration tests
```

Canonical repository:
[PURETASK/Football-Program](https://github.com/PURETASK/Football-Program)

# NFL FIDOS Tutorial

## 1. What this project is

NFL FIDOS is an NFL-scoped Football Intelligence and Development Operating System. It connects football knowledge, playbook composition, player development, staff collaboration, film, scouting, analytics, practice planning, game planning, governance, and bounded specialist-agent validation through one evidence-aware operating model.

The system is designed around four principles:

1. Football concepts are modeled compositionally. A label such as “quarters” or “inside zone” is not treated as a complete scheme by itself.
2. Every important recommendation preserves context, source evidence, assumptions, uncertainty, alternatives, and review state.
3. Human authority remains in control of locked artifacts, organization doctrine, approvals, medical/performance escalation, production rollout, and stage advancement.
4. Local validation is useful evidence, but it is never silently treated as production deployment, real-team data, owner approval, or pilot acceptance.

## 2. Current project state

The repository contains the implementation foundation for all 26 Master Plan stages. The current controlled state is:

- Current stage: `STAGE-0`
- Current work package: `STAGE-0A`
- Production implementation: disabled
- Stage advancement: human-controlled
- Regression suite: 546 tests
- Evaluation suite: 97/97 families passing
- Traceability: 479 evidence references resolving

This is a verified foundation, not a claim that every external rollout action has happened. Real organization records, provider credentials, production deployment, and owner decisions must be supplied by authorized people.

## 3. Repository map

| Area | Purpose |
| --- | --- |
| `control/` | Stage manifests, registry, gates, evaluation manifest, traceability, and safety evidence |
| `src/nfl_fidos/` | Core domain models, API router, services, repositories, validators, workers, and governance |
| `frontend/` | Incrementally migrated React and TypeScript application, design system, independent workspaces, and full-screen Play Designer |
| `ui/operator-dashboard.html` | Served operator dashboard and local validation workspaces |
| `ontology/` | Canonical football terms, aliases, relationships, and team-usage validation |
| `scheme/` | Offensive, defensive, and lineage-aware scheme foundations |
| `playbook/` and `visual/` | Play records, role views, visual notation, timelines, and what-if isolation |
| `development/`, `performance/`, `special_teams/` | Player development, performance boundaries, and special-teams systems |
| `analytics/`, `knowledge/`, `rules/` | Metrics, provenance, research, source hierarchy, and rule authority |
| `contracts/` | JSON schemas and interface contracts |
| `scripts/` | Rehearsals, audits, preflights, smoke checks, and validation commands |
| `runbooks/` | Human operating procedures and safety boundaries |
| `tests/` | Regression, API, permission, tenancy, safety, rehearsal, and UI contract tests |

## 4. Prerequisites

Use the bundled workspace Python when available. The project itself is dependency-light, but DOCX conformance auditing requires `python-docx` in the document runtime.

PowerShell setup:

```powershell
$env:PYTHONPATH = "src"
$runtimePython = "C:\Users\onlyw\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
```

If using a normal Python installation, install the project and the test/document tooling required by your environment. Do not put production secrets in the repository.

## 5. The verification loop

Run the complete local verification loop from the repository root:

```powershell
& $runtimePython -m unittest discover -s tests -q
& $runtimePython scripts/run_evals.py
& $runtimePython scripts/validate_control_plane.py
& $runtimePython scripts/audit_master_plan.py
& $runtimePython scripts/validate_traceability.py
& $runtimePython scripts/validate_deployment_infrastructure.py
& $runtimePython scripts/validate_browser_evidence.py
& $runtimePython scripts/project_audit.py
```

The project audit reports `foundation_verified` only when the source-plan audit, traceability, evaluations, and control safety checks pass. It deliberately reports `completion_claimed: false` while external requirements remain.

## 6. Start the local dashboard

Start the non-production HTTP adapter:

```powershell
& $runtimePython scripts/serve_local.py --host 127.0.0.1 --port 8766
```

Open `http://127.0.0.1:8766/`. The dashboard is a local operator surface for reviewing evidence and rehearsing bounded workflows. It does not enable production or bypass authentication.

The served runtime exposes:

- `/health` — runtime health response.
- `/v1/control` — current stage and work package.
- `/v1/evals` — deterministic evaluation results.
- `/operator-dashboard` — the same dashboard shell.
- Domain-specific authenticated routes documented in `NFL_FIDOS_API.md`.

Run the read-only dashboard smoke check against the local service:

```powershell
& $runtimePython scripts/dashboard_smoke.py http://127.0.0.1:8766
```

### Start the integrated React application

Build the migrated frontend, then start the Python API and static host:

```powershell
npm ci --prefix frontend
npm test --prefix frontend
npm run build --prefix frontend
$env:PYTHONPATH = "src"
$env:NFL_FIDOS_AUTH_SECRET = "local-demo-secret-change-me-32-characters"
$env:NFL_FIDOS_DATABASE = ".runtime\nfl_fidos.sqlite3"
python -m nfl_fidos.server
```

Open `http://127.0.0.1:8080/app`. Today, Playbook, Film, Practice, Scouting, Game Plan, Player, Admin, and Reviews have distinct React routes. The Play Designer is at `/app/playbook/designer/:designId` and includes an eight-step tutorial that opens until completed and can be restarted from its toolbar.

## 7. How the dashboard is organized

The dashboard follows a progressive-disclosure pattern:

1. Program status: service health, current stage, evaluation state, and approval state.
2. Governance: Stage 0 evidence, acceptance records, audit visibility, and release boundaries.
3. Organization readiness: onboarding, population readiness, operating-bundle composition, and pilot evidence.
4. Football workspaces: Today, Playbook, Film, Practice, Scouting, Game Plan, Player Development, Admin, and Reviews. Migrated React menu items open separate pages rather than one long dashboard document.
5. Controlled runtime surfaces: local agent validation, media workers, source operations, and bounded operational actions.

The interface must always show whether a result is informational, under review, approved, locked, validation-only, or production-authorized. A green local test does not mean production is enabled.

## 8. Stage 0 owner approval

Stage 0 is the discovery and control gate. It is ready for owner review when the registry, references, metadata, gap audit, and exit-gate checks pass.

Generate the value-free owner packet:

```powershell
& $runtimePython scripts/stage0_owner_approval_preflight.py
```

The authorized program owner reviews:

- `control/stage-0a-registry.json`
- `control/stage-0-gap-audit.json`
- `control/stage-0-exit-gate.json`
- `NFL_FIDOS_SOURCE_AUDIT.md`
- `NFL_FIDOS_IMPLEMENTATION_STATUS.md`

Approval evidence is submitted through the authenticated `POST /v1/control/stage-0-approval` route. It records evidence only. It does not edit the manifest, advance the stage, enable production, or authorize deployment.

## 9. Organization onboarding sequence

When the program owner identifies the first operating organization:

1. Create a draft organization context.
2. Attach the approved team and source references.
3. Create the draft terminology bundle.
4. Populate the organization-specific packages without fabricating missing data.
5. Run the population-readiness checklist.
6. Compose the 13-component operating bundle.
7. Submit it for owner review.
8. Approve each applicable package through its role-controlled endpoint.
9. Keep activation and production rollout separate from package approval.

Use `runbooks/organization-population-readiness.md` and `runbooks/organization-operating-bundle.md` for the detailed contracts. Synthetic rehearsals prove package composition only; they do not create real organization data.

## 10. Core football workflow

The central football loop is:

```text
source/evidence -> concept or play draft -> role view -> teaching artifact
      -> measurable drill -> review -> owner decision -> locked artifact
```

A play can be compiled and displayed before it is approved. A role-specific view can be generated before it is locked. A what-if scenario can be explored without replacing the canonical play. This separation is intentional.

## 11. Agent runtime

The local agent runtime is a controlled validation rehearsal, not a provider-connected production agent system.

Allowed local use:

- Program owners and validators.
- Declared agent role and capability.
- Organization-scoped signed token.
- Local adapter only.
- No provider call.
- No canonical artifact write.
- No production activation.

See `runbooks/agent-runtime-api.md` and `runbooks/local-agent-adapters.md`.

## 12. Media, retention, and source safety

Media assets must preserve authorization, organization scope, integrity metadata, bounded clips, and provenance. Retention planning and scans are non-destructive by default.

Managed-media retention execution is a separate boundary:

- Dry-run is the default.
- A program-owner role and explicit approval reference are required.
- Only regular files inside the managed root are eligible.
- Unknown timestamps are retained for review.
- Asset records remain as auditable tombstones.
- Production execution is blocked while the Stage 0 manifest disables production.

See `runbooks/media-retention.md`, `runbooks/media-retention-execution.md`, and `runbooks/media-storage.md`.

## 13. UX and UI design system

The React application uses a reusable token and component system with a navy football-operations shell, light working surfaces, semantic green/amber/red states, deliberate typography, layered cards, responsive grids, and high-contrast focus states. The current UI pass includes:

- Inter/system sans-serif typography.
- Responsive card grids and forms.
- Role-aware desktop navigation and a tablet navigation drawer.
- Keyboard skip link.
- Visible focus rings.
- Reduced-motion support.
- Semantic safety notices.
- Wrapped long values and result text to prevent clipping.
- Consistent primary and secondary button treatment.
- A visible `About this page` description on every migrated route.
- Reusable description boxes that state purpose, operation, audience, output, and authority boundary.
- Feature cards that identify purpose, operating method, inputs, outputs, and current control state.
- A full-screen Play Designer with permanent contextual descriptions and a restartable eight-step tutorial.

When adding a migrated workspace, use the tokens in `frontend/src/styles/tokens.css` and the shared React components rather than introducing arbitrary colors or spacing. Every workspace must have a clear heading, visible page purpose, system description, feature descriptions, labeled controls, status region, result feedback, an authentication boundary where needed, and an explicit authority or safety statement. Keep the legacy dashboard stable until the feature-parity audit permits retirement.

## 14. How to add a new feature

1. Add or update the domain model in `src/nfl_fidos/`.
2. Define or update its JSON contract in `contracts/`.
3. Enforce organization scope through `TenantRepository`.
4. Define role permissions and human-approval boundaries.
5. Add an authenticated API route in `src/nfl_fidos/api.py`.
6. Add the dashboard surface only after the API contract is stable.
7. Add unit, API, tenancy, negative-path, and safety tests.
8. Add a runbook describing the operator action and limitations.
9. Add the files to the requirements traceability ledger.
10. Run the complete verification loop.

Do not silently add a production mutation to a local rehearsal. Use explicit `execute` flags, approval references, environment checks, and evidence records.

## 15. Professional play creation

Structured authoring is implemented across the canonical Python services and the dedicated React Play Designer. The shared model covers players and alignments, route/motion/run/block/rush/coverage paths, arrow semantics, timing, offensive concepts, defensive front/coverage packages, validation, collaboration, publishing, role views, and exports. Research and the full feature inventory are in [`research/playbook-creation-research.md`](research/playbook-creation-research.md); the implementation blueprint is [`PLAY_DESIGNER_BUILD_GUIDE.md`](PLAY_DESIGNER_BUILD_GUIDE.md); the in-app walkthrough is documented in [`runbooks/play-designer-tutorial.md`](runbooks/play-designer-tutorial.md).

The recommended build sequence is:

1. Build reusable formation, personnel, front, coverage, route, motion, and protection templates.
2. Add a layered canvas with snapping, handles, annotations, undo/redo, and what-if overlays.
3. Add legality and completeness linting before a design can be marked validated or game-ready.
4. Render role views, animation, print/PDF, wristband, call-sheet, and accessible text views from the same design record.
5. Keep organization aliases and call words separate from normalized football terms so every program can teach its own language.

The React canvas is a locally working authoring surface, but advanced parity items, moderated staff/player validation, team-approved data, Stage 0 owner approval, and external organization/provider setup still govern production readiness.

## 16. Troubleshooting

### Imports fail from the repository root

Set `PYTHONPATH=src` or use the project’s configured package installation.

### The DOCX audit cannot run

Use the bundled document Python runtime with `python-docx` installed.

### The dashboard says unavailable

Confirm the local server is running, check `/health`, then inspect the browser console and server output. Authentication-protected routes should fail closed without a valid organization-scoped token.

### A production readiness report is blocked

That is expected when the external secret source, deployment database, monitoring registration, scheduler registration, provider tools, or Stage 0 authorization is missing. Do not bypass the blocker.

### A test or audit changes state

Stop and inspect the command. Local rehearsals should use temporary workspaces and should report `external_state_changed: false` unless an explicitly authorized external operation is being performed.

## 17. External handoff

Generate the current handoff packet with:

```powershell
& $runtimePython scripts/external_action_handoff.py
```

This groups the remaining requirements by program owner, operating organization, deployment owner, and pilot stakeholders. It is the correct starting point when moving from the verified local foundation to authorized real-world implementation.

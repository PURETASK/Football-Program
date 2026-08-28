# NFL FIDOS System Catalog and User Guide

Version: 2026-08-28

This catalog describes the systems, pages, services, engines, controlled agent roles, data foundations, and operating workflows currently represented in the repository. It is an implementation inventory, not a claim that production deployment, real organization data, provider integrations, pilot acceptance, or owner approvals have occurred.

## 1. Read the status labels first

| Label | Meaning |
| --- | --- |
| Implemented locally | The repository contains the behavior and local tests or rehearsals for it. |
| Validation-only | It can be exercised as a bounded local rehearsal, but it does not activate a provider, production tenant, or irreversible operation. |
| Human-gated | A human owner, coach, rules authority, or qualified staff member must approve or resolve it. |
| Production-gated | Deployment, managed storage, secrets, monitoring, real organization data, or external provider setup is still required. |
| Planned / incomplete | The contract or foundation exists, but the production-grade capability or evidence is not complete. |

The central rule is: a passing local test proves that the local implementation behaves as tested. It does not prove production readiness, live provider execution, real-team adoption, Stage 0 approval, or Stage 25 acceptance.

## 2. Application entry points and page map

The React application is mounted at `/app` and keeps the Python API and football-domain services authoritative. Each primary navigation item is its own route.

| Route | Page | Main use |
| --- | --- | --- |
| `/app` | Today | Command center for current work, priorities, blockers, reviews, and delivery state. |
| `/app/inbox` | Unified Operations Inbox | Review pending actions, overdue work, failed validations, notifications, and deep links. |
| `/app/playbook` | Playbook Library | Search, filter, inspect, compare, and open play designs. |
| `/app/playbook/designer/:designId` | Play Designer | Create and teach an offensive or defensive play in a dedicated full-screen workspace. |
| `/app/film` | Film Intelligence Studio | Work with authorized video, clips, observations, telestration, and evidence links. |
| `/app/practice` | Practice and Install Builder | Schedule periods, plays, drills, reps, players, attendance, and outcomes. |
| `/app/scouting` | Scouting Tendency Explorer | Query opponent tendencies and create evidence-qualified reports. |
| `/app/game-plan` | Game Plan Release Room | Assemble, compare, approve, lock, and roll back weekly game-plan releases. |
| `/app/player` | Player Learning Hub | Deliver role-specific lessons, step reveals, quizzes, mastery, and practice links. |
| `/app/roster` | Roster and Personnel | Maintain organization-scoped players, positions, availability, depth charts, and packages. |
| `/app/analytics` | Outcome Analytics | Compare intended design with practice/game outcomes and uncertainty. |
| `/app/delivery` | Game-Week Delivery Center | Manage deadlines, owners, packet readiness, and delivery tasks. |
| `/app/collaboration` | Staff Collaboration | Review threads, comments, assignments, mentions, presence, and resolution state. |
| `/app/reviews` | Reviews and Approvals | Inspect governed review requests and human decisions. |
| `/app/admin` | Admin and Governance | Inspect system state, governance, readiness, security, and controlled operations. |
| `/app/admin/stage-25` | Stage 25 Acceptance | Record specification acceptance evidence through the governed route. |
| `/app/admin/population-readiness` | Population Readiness | Show which organization operating-bundle inputs are present or missing. |

Every migrated page is expected to expose a heading, description, audience, output, current status, labeled controls, feedback, and authority/safety boundary through the shared design system.

## 3. Shared application shell and UI system

### What it provides

- Navy football-operations shell with light working surfaces.
- Shared design tokens for color, spacing, radii, typography, focus, semantic status, and responsive layout.
- Role-aware navigation and route-level lazy loading.
- Keyboard skip link, focus rings, dialog focus management, reduced-motion handling, and responsive tablet layout.
- Reusable page headers, description boxes, workbench frames, tabs, state panels, metric cards, status pills, record lists, inspectors, empty states, field thumbnails, play cards, session dialog, command palette, and brand mark.
- Distinct page descriptions so users understand what a feature is for before operating it.

### How to use it

1. Open `/app`.
2. Choose a workspace from the navigation or command palette.
3. Read the page description and status region before changing records.
4. Use the page’s primary action, then inspect the result feedback and audit state.
5. Use the browser Back button or navigation to move between independent pages.

### Current boundary

The React migration is operational locally. Legacy dashboard retirement still requires a feature-parity audit, browser/tablet/accessibility evidence, and production rollout decisions.

## 4. Today and Operations

### Today command center

Aggregates the organization’s current work into a role-oriented starting point: urgent work, reviews, readiness, delivery, and connected football workspaces.

### Unified Operations Inbox

Aggregates:

- Pending reviews and approval requests.
- Overdue or due-soon tasks.
- Failed or incomplete validations.
- Missing evidence and unresolved conflicts.
- Practice preparation and scouting updates.
- Game-plan decisions and release blockers.
- Notifications, owners, urgency, due dates, acknowledgement, and safe deep links.

How to use: open `/app/inbox`, filter by owner/status/urgency/type, open the linked workspace, perform the authorized action, and acknowledge the notification when appropriate.

## 5. Playbook and Play Designer

### Playbook Library

Provides searchable visual play cards, metadata, status, tags, and direct navigation into a design. It is the catalog-level entry point; the designer is the authoring workspace.

### Play Designer model

A design contains organization scope, unit, formation/front/coverage/personnel/concept/rule profile, players, structured elements, timeline state, teaching state, review state, version lineage, and export metadata.

### Authoring tools

- Player icons and position-aware player profiles.
- Position toolkit with compatible asset and template suggestions.
- Drag-to-draw routes and paths.
- Route handles for start, stem, break, and finish.
- Landmarks, depth presets, angle presets, stems, breaks, timing, and multi-path branches.
- Motions, shifts, releases, runs, blocks, pulls, traps, combos, screens, protections, rushes, stunts, coverage, rotations, checks, reads, and teaching annotations.
- Multi-select, grouping, copy/paste, mirroring, layers, locking, snapping, alignment, and canvas controls.
- Offensive and defensive assignment inspectors.
- Defensive front, technique, alignment, gap ownership, exchange partners, pressure paths, coverage-shell boxes, rotation sequence, and replacement responsibility.
- Route collision detection with intentional-crossing explanation fields.
- What-if overlays so an experiment does not silently replace the canonical design.

### Asset library and templates

The registry contains professional categories for formations, personnel, routes, route variations, motions, runs, protections, blocks, fronts, techniques, coverages, pressures, blitzes, stunts, rotations, checks, annotations, and teaching aids. Assets support search, category/unit filtering, thumbnails, aliases, compatibility rules, lifecycle status, approval metadata, deprecation, and migration.

Templates can be applied as replacement or layered stencils. A selected subset of assignments can be captured as a reusable stencil. Child templates can inherit from parent templates; local assignments override inherited assignments. Preview and materialized assignments preserve inherited/local provenance.

How to use:

1. Open `/app/playbook` and choose a play, or open `/app/playbook/designer/new` for a new draft.
2. Choose the unit, formation/front, personnel, coverage, and concept.
3. Select a player icon on the canvas or in the position toolkit.
4. Review the position-aware suggested assets and templates.
5. Click or drag an asset to materialize it; edit its handles and inspector fields.
6. Use select/group/mirror/layer/lock tools to organize the diagram.
7. Use validation before review; do not treat an invalid or draft play as game-ready.
8. Save, request review, branch for alternatives, or publish only through the governed lifecycle.

### Timeline and teaching

The timeline supports element timing, phase labels, playback, pause markers, narration, QB reads, ball handling, route phases, block/rush exchanges, coverage rotations, and teaching sequence. Teaching views can filter by role, hide unrelated assignments, reveal steps, expose accessible text, attach quizzes, record mastery, and link practice objectives.

How to use: open the timeline, select an element, set start/end timing and phase, add markers/narration/read steps, preview playback, then open the teaching view and choose a position or audience.

### Versioning and collaboration

Supports draft save, revision history, review requests, comments, replies, resolution/reopen, presence, branching, visual source-vs-variant comparison, metadata and element-level diffs, merges, immutable publish snapshots, checksums, rollback, and release checks.

Variant batches are governed by `contracts/play-design-variant.schema.json`: each look must have a label and at least one bounded look-level change, may include no more than 64 explicit assignment transformations, and remains a draft child until human review and publication. The schema documents the integration boundary; the Python service remains authoritative for element existence, supported fields, legality, and tenant authorization.

How to use: create a branch for a competing look, compare it with the source, review added/removed/changed assignments, request staff review, resolve comments, merge only when authorized, and publish a locked snapshot only after validation.

### Exports

Supports PDF, SVG, PNG, HTML/JSON data, call-sheet output, wristband CSV/layouts, install sheets, accessible text, branding, black-and-white options, page numbering, source manifests, hashes, and export preflight. Export validation follows the selected rule profile's player count and fails closed when a local-adoption profile such as youth or local-variant flag football lacks its approved local rule source.

How to use: run export preflight first, correct blockers, select audience/layout/branding/print options, export, and retain the manifest with the artifact. Production printer/device validation remains a gate.

### Legality and quality

Validation covers structure, completeness, formation/eligibility, alignment, motion/reset, personnel, assignment conflicts, route collisions, protection conflicts, defensive gap/fit conflicts, coverage gaps, rule profiles, explainable findings, and coach override workflows. Profiles exist for NFL, NCAA, high school, youth, and flag contexts at varying depth.

How to use: select the rule profile, run validation, inspect each finding’s explanation and severity, fix the design or submit an authorized override with rationale and evidence, then rerun validation.

## 6. Film Intelligence Studio

### Capabilities

- Authenticated media loading and organization scope.
- Bounded video playback and frame stepping.
- Timeline control and frame-accurate observations.
- Pointer telestration and drawing tools.
- Player tracking links.
- Bounded clip creation.
- Transcript-backed voice notes with size safety limits.
- Annotation sessions, playlists, quizzes, and source-linked observations.
- Searchable stream metadata and authenticated media jobs.
- Direct evidence links into scouting, player development, game plan, playbook, and analytics.

How to use: register or select an authorized asset, open `/app/film`, choose a clip/session, pause and frame-step to the evidence point, annotate, attach players/tags, save the observation, and hand it off to a downstream review. Unauthorized or weakly sourced media must not become canonical evidence.

## 7. Practice and Install Builder

### Capabilities

- Practice plans and period builder.
- Drag/keyboard period ordering.
- Play and drill selectors tied to the Playbook and drill corpus.
- Install phase, objective, position group, roster IDs, attendance policy, workload envelope, reps, and print preference.
- Roster-linked attendance.
- Period-specific practice outcomes.
- Practice responsibility and phase/exchange outcome capture.
- Printable practice cards and analytics linkage.

How to use: open `/app/practice`, create a practice, add periods, select plays/drills and position groups, set reps/time/objectives, record attendance and outcomes, then print or link the results into Player and Analytics.

## 8. Scouting Tendency Explorer

### Capabilities

Queries opponent behavior by down, distance, field zone, personnel, formation, motion, front, coverage, pressure, and game situation. Results preserve sample size, confidence, trends, source clips, evidence, contradictions, limitations, and review state.

How to use: open `/app/scouting`, define filters, inspect sample/confidence and source evidence, review contradictions, create a report, and send it to Game Plan only when it is explicitly under human review.

## 9. Game Plan Release Room

### Capabilities

- Weekly option/counter assembly.
- Links to scouting evidence, play designs, practice priorities, install materials, call sheets, and wristbands.
- Immutable snapshots.
- Dependency manifests and unresolved-reference checks.
- Renderer version and release hash.
- Changed-field summaries.
- Approval gates, locking, rollback, and release readiness.

How to use: open `/app/game-plan`, assemble the weekly package, resolve dependencies, create a snapshot, inspect what changed, obtain the authorized approval, lock the release, and use rollback only through the governed path.

## 10. Player Learning Hub

### Capabilities

- Privacy-scoped assignments and lessons.
- Position-group and player-only views.
- Step-by-step play reveal.
- Quizzes, coach feedback, mastery, due dates, and practice linkage.
- Accessible text views.
- Offline cache for approved content with encrypted local storage boundaries.

How to use: open `/app/player`, choose the assigned lesson, reveal the play by step, complete the quiz, review feedback, and connect the lesson to the relevant practice period. Coaches can inspect mastery without exposing another player’s private data.

## 11. Roster and Personnel System

### Capabilities

Organization-scoped player identity, aliases, positions, availability, depth charts, personnel packages, eligibility, role groups, staff ownership, and status. It powers Player, Practice, Play Designer, Game Plan, and Scouting selectors.

How to use: open `/app/roster`, add or import authorized player records, assign positions and availability, build depth charts/packages, and verify that downstream workspaces use the correct organization-scoped IDs.

## 12. Collaboration and Notifications

### Capabilities

- Cross-workspace threads and linked entities.
- Replies, mentions, assignments, due dates, priority, notifications, resolution/reopen, activity feed, presence heartbeat, and audit-backed state changes.
- Play Designer collaboration events, SSE with short-poll fallback, branch/review context, conflict visualization, and outbox support.

How to use: open `/app/collaboration` or use the comments/review controls inside a workspace, mention an authorized teammate, assign a due date, resolve only when the issue is addressed, and use the activity history for audit context.

## 13. Outcome and Performance Analytics

### Capabilities

- Structured intended-versus-actual outcomes.
- Practice and game evidence links.
- Play, assignment, film, scouting, game-plan, and mastery lineage.
- Context-aware metrics, denominator preservation, sample size, confidence, Wilson uncertainty, caveats, and report composition.
- Performance ingestion boundaries and non-diagnostic health-signal escalation.

How to use: open `/app/analytics`, choose a context and sample, inspect denominators and uncertainty, compare intent with outcome, and export or hand off only with limitations preserved.

## 14. Game-Week Delivery Center

### Capabilities

Calendar/deadline tasks, owner assignment, completion audit, packet checklists, readiness summaries, owner notifications, safe deep links, and packet composition for coaches, players, coordinators, and administrators.

How to use: open `/app/delivery`, create or inspect tasks, assign an owner and due date, attach required artifacts, complete tasks with evidence, and verify packet readiness before distribution.

## 15. Admin, governance, and control plane

### Capabilities

- Stage manifests and work-package registry.
- Master-plan audit and traceability.
- Stage 0 owner packet and approval evidence route.
- Stage 25 specification acceptance route.
- Organization onboarding and population readiness.
- Operating-bundle composition and approval boundaries.
- Governance inbox and change control.
- Rule-source refresh review.
- Deployment preflight and readiness.
- Pilot readiness and evidence collection.
- Security threat model, tenant isolation checks, audit verification, rate limits, redaction, retention controls, and recovery rehearsals.

How to use: open `/app/admin`, inspect current stage and blockers, use the specific governed route for the action, and keep production disabled until the required human and external gates are satisfied.

## 16. Knowledge, ontology, scheme, and rules engines

### Ontology engine

Canonical football terms, aliases, relationships, naming standards, team terminology bundles, ambiguity detection, and organization alias resolution. It keeps local team language separate from normalized terms.

### Scheme engine

Compositional offensive, defensive, and special-teams models; scheme families; personnel fit; strengths/weaknesses; counters/counter-counters; install requirements; doctrine lineage; and play-to-scheme compatibility.

### Rules engine

Source-linked authority model, jurisdiction/effective-period handling, rule profiles, exceptions, refresh candidates, review state, and escalation. It separates authoritative rule facts from strategy recommendations.

The Play Designer quality gates also compare the declarative `rules/play-design-rule-profiles.json` catalog with the executable legality policy. The check covers player count, line count, motion limits, blocking/contact policy, rush distance, local-adoption requirements, and source presence. Youth remains intentionally uncommitted until an adopting league provides its local rule source and values.

### Evidence and knowledge engine

Claim classification, provenance, source authorization, evidence strength, context, sample limitations, knowledge search, source refresh, and disagreement preservation.

## 17. Media, storage, and retention systems

- Media registration with authorization, organization scope, integrity, capture time, duration, and source metadata.
- Clip and transformation jobs.
- FFmpeg/FFprobe local smoke rehearsal.
- Managed-storage scale rehearsal with path isolation and digest checks.
- Retention planning and non-destructive scans.
- Owner-approved retention execution boundary with tombstones and unknown-timestamp protection.
- Encrypted offline cache and offline collaboration outbox.

These are designed to fail closed around authorization and destructive operations. Managed external media storage and production retention execution remain deployment-gated.

## 18. Controlled agent runtime

The repository defines 16 callable, inactive-by-default roles. They are controlled specialist contracts, not autonomous production agents.

| ID | Role | Primary capability |
| --- | --- | --- |
| AGT-001 | Orchestrator | Routes bounded workflows and assembles handoffs. |
| AGT-002 | Quarterback specialist | Teaches and assesses quarterback execution. |
| AGT-003 | Position specialist | Teaches position technique and assignment behavior. |
| AGT-004 | Coach pedagogy specialist | Designs teaching and coaching evaluation pathways. |
| AGT-005 | Offensive architecture specialist | Composes and compares offensive structures. |
| AGT-006 | Defensive architecture specialist | Composes defensive structures and responses. |
| AGT-007 | Play compiler validator | Validates schema, assignment, and rule completeness. |
| AGT-008 | Practice architect | Connects objectives, drills, plays, load, and practice periods. |
| AGT-009 | Film intelligence specialist | Produces clip-traceable observations and QA. |
| AGT-010 | Opponent scout | Produces contextual opponent tendencies and matchups. |
| AGT-011 | Analytics specialist | Computes context-aware metrics and uncertainty. |
| AGT-012 | Game-plan council | Compares weekly options, counters, and triggers. |
| AGT-013 | NFL rules authority | Cites and explains authoritative rule facts. |
| AGT-014 | Nuance and context council | Qualifies uncertainty, evidence, exceptions, and context. |
| AGT-015 | Disagreement council | Preserves and compares competing interpretations. |
| AGT-016 | Permission and safety validator | Enforces least privilege, tenancy, safety, and promotion blockers. |

How the runtime works: a permitted caller submits organization context, role, capability, payload, evidence, and requested action; the runtime validates the contract and permissions; a local adapter may produce a deterministic rehearsal result; the handoff preserves source, context, uncertainty, and review requirements. No agent may silently approve, publish, lock, alter canonical history, or make a medical/high-consequence decision.

## 19. Persistence, API, contracts, and audit

- Python service facade and domain services.
- SQLite repository for local persistence and revision history.
- Tenant repository for organization scope.
- JSON schemas for plays, schemes, compatibility, agents, governance, performance, onboarding, operating bundles, and exports.
- Authenticated API with explicit route allowlists.
- Append-only audit events and traceability ledger.
- Revision checks, release hashes, renderer checksums, and immutable snapshots.
- Offline draft recovery, autosave, retry, remote revision decisions, and conflict merge helpers.

How to use: treat API contracts and domain services as authoritative; use the React pages as the operator surface; never bypass tenant/auth checks by writing directly to local files or browser state.

## 20. Verification and operations toolkit

The repository includes scripts for:

- Full Python regression tests.
- Frontend tests, typecheck, and production build.
- Evaluation suites.
- Control-plane and master-plan audit.
- Traceability validation.
- Browser evidence validation.
- Deployment and environment readiness.
- Database, media, backup, incident, monitoring, secret-manager, source, and provider rehearsals.
- Demo seeding and complete demo-data deletion.
- Pilot rehearsal and organization operating-set rehearsal.

Representative local commands from the repository root:

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -q
python scripts/run_evals.py
python scripts/validate_control_plane.py
python scripts/audit_master_plan.py
python scripts/project_audit.py
npm.cmd test --prefix frontend -- --run --maxWorkers=1
npm.cmd run typecheck --prefix frontend
npm.cmd run build --prefix frontend
```

## 21. Seed data and safe demo use

The project includes demo-data generation and deletion scripts. Seed data is synthetic and must remain clearly labeled. Use it to inspect the page flows, then remove it with the deletion script before treating the database as real.

Typical workflow:

1. Read `runbooks/demo-seed-data.md`.
2. Run the seed script with an explicitly temporary local database.
3. Play through Today, Playbook, Designer, Film, Practice, Scouting, Game Plan, Player, Roster, Analytics, Delivery, Collaboration, and Reviews.
4. Capture any usability defects.
5. Run the deletion script against the exact demo database and verify the records are gone.

## 22. What is not yet proven complete

The implementation foundation is extensive, but the following remain external or production gates:

- Stage 0 owner approval and Stage 25 specification acceptance.
- Real organization terminology, rosters, schedules, media, and approved play data.
- Production deployment, database/media storage, secrets, monitoring, backups, and rollback rehearsal.
- Provider-specific adapters and live integrations.
- Moderated coach, coordinator, and player pilot sessions with measured usability outcomes.
- Full cross-browser, tablet, screen-reader, contrast, reduced-motion, printer/device, and visual-regression evidence.
- Production-grade collaboration convergence testing with multiple real clients.
- Complete rule-profile review by the appropriate authorities.
- Legacy dashboard feature-parity audit before retirement.

## 23. Source-of-truth files

- `NFL_FIDOS_IMPLEMENTATION_STATUS.md` — current implementation and evidence summary.
- `NFL_FIDOS_TUTORIAL.md` — operator/developer tutorial.
- `PLAY_DESIGNER_BUILD_GUIDE.md` — play-designer architecture and build guide.
- `PLAY_DESIGNER_COMPETITIVE_BENCHMARK.md` — competitive capability target and reconciliation.
- `contracts/play-design-variant.schema.json` — machine-readable contract for bounded look variants and assignment transformations.
- `governance/master-plan/NFL_Football_Intelligence_OS_Master_Codex_Plan_v1.0.md` — authoritative master plan.
- `agents/agent-organization-bible.json` — controlled agent roles and handoff rules.
- `control/` — stage, governance, safety, acceptance, and evidence contracts.
- `runbooks/` — step-by-step operational procedures.

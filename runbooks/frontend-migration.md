# React frontend migration

## Current verification correction (2026-08-28)

The current checkout passes 199/199 frontend tests and 626/626 Python regression tests. The production frontend build and TypeScript typecheck also pass. Older dated verification paragraphs below are preserved as historical records; use this correction for the current baseline.

The new interface is an incremental replacement, not a backend rewrite. The Python API, repositories, football validation, approval, versioning, export, and collaboration services remain authoritative.

## Migration boundary

| Surface | Route | State |
| --- | --- | --- |
| React application shell | `/app` | Active |
| Today command center | `/app` | Migrated |
| Visual Playbook library | `/app/playbook` | Migrated |
| Full-screen Play Designer | `/app/playbook/designer/:designId` | Primary React authoring slice migrated; parity gaps listed below |
| Inbox, Roster, Analytics, Delivery, Collaboration, Film, Practice, Scouting, Game Plan, Player, Admin | `/app/...` | Independently lazy-loaded operational workbenches with live API data, role-aware controls, search, record inspection, authoring, release/delivery controls, collaboration, and explicit authority boundaries |
| Reviews and Approvals | `/app/reviews` | Governed decision center with evidence inspection, return/reject decisions, and canonical change-request approval; generic workflow approval bypasses are blocked |
| Legacy operator dashboard | `/operator-dashboard` | Preserved until the documented feature-parity audit passes |

Do not remove the legacy dashboard while a migrated route links to it or while a workflow in the parity boundary remains legacy-only.

## Play Designer capabilities now in React

- Organization-scoped load of canonical plays, templates, legality results, immutable version history, comments, presence, and the professional asset registry.
- Searchable and filterable offense/defense asset palette with compatibility indicators and direct tool activation.
- Canonical 100-by-53 SVG field with offense/defense symbols, yard lines, hashes, line of scrimmage, route arrows, motion, runs, blocks, rushes, stunts, coverage paths, and coaching annotations.
- True pointer drag-to-draw paths, editable path handles, player dragging, keyboard object selection and nudge, multi-select, grouping, duplication, mirroring, deletion, snapping, zoom, layers, visibility, and locking.
- Per-assignment start/end timing, timeline seek/play/reset, phase reveal, player motion, teaching markers, and selected-assignment timing windows.
- Three-second autosave to the Python API, optimistic revision checks, explicit conflict recovery, undo/redo history, immutable save snapshots, tab-stable staff presence, and a reconnecting authenticated SSE event stream with query invalidation and short-poll fallback behavior.
- Review request, human-controlled publish, branch creation, linked comments, legality findings, version history, and production export dialog for the server's validated play-card, call-sheet, wristband, and install-sheet formats.
- Dedicated responsive workspace, compact accessible controls, focus-trapped export dialog, reduced-motion styling, and a lazy-loaded route chunk that keeps the general shell bundle separate.
- Eight-step in-app tutorial covering the asset registry, canvas, editing controls, animation timeline, football inspector, legality/review lifecycle, publishing, branching, and exports. It is non-destructive, keyboard navigable, completion-aware, and restartable from the toolbar.
- Visible contextual descriptions for the asset library, field canvas, timeline, Inspect, Layers, Checks, and Review regions so the interface explains both purpose and operation at the point of use.

## Page and feature description contract

Every migrated route must answer five questions without requiring external documentation:

1. What is this page or system for?
2. How does it operate?
3. Who uses it?
4. What does it produce?
5. What authority, safety, or migration boundary applies?

The shared `DescriptionBox` component provides that contract at page and section level. Operational workspace feature cards additionally identify purpose, operating method, input, output, and current control status. Inbox, Roster, Analytics, Delivery, Film, Practice, Scouting, Game Plan, Player, Admin, and Reviews use shared accessible workbench primitives while retaining distinct data, mutations, metrics, workflows, and role visibility. They do not redirect to sections of the legacy dashboard.

## Operational workbenches now in React

- Operations Inbox: aggregate reviews, due work, blockers, owners, unread notifications, and safe deep links; notification acknowledgement is authenticated and audited.
- Roster: maintain organization-scoped players, positions, availability, depth charts, and personnel packages with player privacy filtering.
- Analytics: inspect lineage-complete observations, uncertainty, outcome comparisons, and staff-ready reports.
- Delivery: schedule game-week tasks, assign ownership, complete handoffs, and inspect packet/release readiness without silently publishing.
- Collaboration: open organization-scoped cross-system threads, reply with mentions, assign owners and due dates, resolve/reopen discussions, read recipient-scoped notifications, inspect activity, and show expiring staff presence without taking over domain approvals.
- Film: inspect assets, clips, observations, playlists, annotation sessions, and voice notes; use bounded video playback, frame stepping, telestration, frame-linked player tracking, transcript-backed voice capture, and clip creation.
- Practice: inspect saved plans and load findings; drag or keyboard-reorder detailed periods; connect the live Roster, Playbook, and filtered canonical Drill catalogs to period assignments; retain manual play/drill IDs, attendance policy, install phase, and print preferences; record roster-linked present/absent/limited/late/excused participation with human-review flags.
- Scouting: filter profiles, reports, matchups, and evolution records; use the down/distance/zone/personnel/formation/motion/front/coverage/pressure tendency explorer; compose uncertainty-aware reports that remain under human review.
- Game Plan: inspect the weekly plan, situation/counter matrix, evidence, and staff threads; create immutable release snapshots with dependency manifests and hashes, expose linked/unresolved evidence, approve/lock, compare changed fields, and owner-rollback without auto-publication.
- Player: provide privacy-scoped assignments, lessons, step-by-step read reveal, mastery, development plans, quiz history, role-authorized assignment creation, and privacy-scoped offline cache fallback.
- Admin: manage organization context and source metadata, request authorized refreshes, inspect Stage 0 and pilot readiness, and submit owner evidence only at the correct gate.
- Reviews: search and filter the queue, inspect blockers and evidence, return or reject items, and expose approval only when a canonical approval workflow exists.

## Deliberate parity boundary

The underlying Python services already support more than this React slice. The following controls must be migrated or verified in React before the legacy Play Designer can be retired:

- Authenticated SSE event consumption, shared staff cursor overlays, threaded comment replies/resolution, encrypted offline collaboration outbox, and visual conflict comparison are now implemented and locally verified.
- Advanced visual element-level version diff/merge conflict resolution, live coediting/offline collaboration, and multi-item publishing/layout composition for Play Designer; basic visual comparison, guarded merge, and multi-play packet export selection are now available, while weekly game-plan release snapshots expose dependency manifests, hashes, renderer versions, changed fields, owner approval/lock, and rollback in the React Release Room.
- Explainable legality-override request and program-owner approval workflows.
- Role-filtered coach/player teaching views, step-by-step read reveal, quizzes, mastery, and practice linkage.
- Multi-play call-sheet composition and advanced wristband/install layout authoring rather than single-play export handoff.
- Automated screenshot baselines across supported browsers, a real screen-reader matrix, measured contrast automation, large-play/tablet performance traces, and moderated role-based pilot evidence.

## Build and verify

From the project root:

```powershell
npm ci --prefix frontend
npm test --prefix frontend
npm run build --prefix frontend
$env:PYTHONPATH = (Resolve-Path '.\src').Path
python -m unittest tests.test_http_server -v
```

Start the integrated server:

```powershell
$env:PYTHONPATH = (Resolve-Path '.\src').Path
$env:NFL_FIDOS_AUTH_SECRET = 'local-demo-secret-change-me-32-characters'
$env:NFL_FIDOS_DATABASE = '.runtime\nfl_fidos.sqlite3'
python -m nfl_fidos.server
```

Open `http://127.0.0.1:8080/app`. Use the synthetic organization `ORG-DEMO-FIDOS-001` with a fresh token from `scripts/issue_demo_token.py`.

## Acceptance checks

- Every stylesheet and JavaScript file referenced by the legacy dashboard returns `200` with the correct media type.
- `/app`, `/app/playbook`, `/app/playbook/designer/:designId`, `/app/film`, `/app/practice`, `/app/scouting`, `/app/game-plan`, `/app/player`, `/app/admin`, and `/app/reviews` survive direct browser refreshes.
- The lazy Play Designer and operational-page chunks return `200` as UTF-8 JavaScript; hashed assets use immutable caching and cannot escape the approved build directory.
- Static integration tests enforce local budgets of 350 KiB for the migrated shell JavaScript, 90 KiB for the designer route, 30 KiB for each independent operational route bundle, and 90 KiB for combined CSS.
- Today and Playbook display canonical organization data and coordinate-derived diagrams after authentication.
- Play Designer loads seeded canonical data and supports pointer and keyboard selection, registry filtering, timeline playback, legality/review panels, focus-managed export, and responsive tablet layout.
- The tutorial opens for an incomplete first-time session, advances through all eight named steps, moves to the Review panel when required, persists only successful completion, and can be restarted from the toolbar.
- Every migrated page exposes a visible page description; every operational workspace exposes system, feature, workflow, and authority descriptions.
- Navigation is filtered by server-returned sections and token role; credentials remain tab-scoped.
- Keyboard access includes skip navigation, visible focus, named icon actions, Escape-close dialogs, field-object selection, and Command/Ctrl+K search.
- Reduced-motion rules are present.

Latest local result: 90/90 frontend tests and 583/583 Python regression tests pass; the focused release/dependency, inbox/collaboration, Scouting tendency, and Practice drill-catalog suites also pass, and 97/97 evaluation families remain the validated evaluation baseline. The production build compiles, each operational route bundle is under the local 30 KiB budget, and generated index CSS is 92.12 kB, below the enforced 90 KiB threshold. Authenticated route/deep-link, asset-serving, organization collaboration SSE with role filtering, Play Designer shared cursor overlay, encrypted offline outbox, revision-aware remote edit handoff with field-level disjoint-edit three-way merge, layout-aware multi-play export with paginated call-sheet/wristband and play-card grid composition, Film approved server-path asset registration with source-root validation/file hashing/provenance, authenticated Film indexing with searchable stream metadata, voice-note plus Playbook-linked telestration/tracking/evidence workflows, Play Designer diff/merge, role-filtered teaching/player view, encrypted offline draft recovery, encrypted Player Learning Hub cache, Scouting Tendency Explorer organization-scoped querying with dimensions, source links, sample/confidence, contradiction handling, and review-thread handoff, Game Plan Release Room frozen source-plan visual diff, Delivery Center five-audience packet readiness/reviewable packet assembly/Operations Inbox blocker routing, Practice roster/Playbook/drill catalog linkage plus catalog-backed period position-group selectors, Admin persisted pilot selection/package/usability inspection, the dedicated Stage 25 acceptance route, authenticated Admin browser verification, local deployment-environment readiness, release dependency, delivery API, and seeded organization checks pass; full moderated pilot, cross-browser/accessibility matrix, deployment, and owner authorization remain pending.

Player, roster, analytics, delivery, scouting, and release authoring now uses organization-scoped roster targets and source-linked catalog pickers for Playbook, Film, Practice, Depth Chart, Personnel Package, Outcome Report, release, practice, packet, film-evidence, and game-plan evidence records, while preserving manual IDs for approved records that are not yet in the catalog.

Admin governance now exposes non-activating pilot readiness, bounded organization selection, pilot delivery-package composition, and usability/accessibility evidence submission through the canonical Python API. Stage 25 specification review is available at `/app/admin/stage-25` as a separate owner-controlled acceptance evidence workflow; it cannot activate production or advance the stage. Organization population readiness is available at `/app/admin/population-readiness` with season-aware checks across all 13 operating-bundle components and explicit non-activating blockers.

Population readiness implementation note: the dedicated route renders the canonical organization population-readiness endpoint as an inspectable matrix. It shows component scope, season, required status, persisted record references, explicit blockers, and read-only activation flags; it cannot create packages, alter permissions, call providers, advance stages, or enable production.

Current verification correction (2026-08-25): the frontend suite now passes 84/84 tests after adding the Stage 25 acceptance and organization population-readiness route contracts; Python remains 566/566 and the production build passes.

Practice attendance addendum (2026-08-25): the Practice workbench now exposes an Attendance view backed by `GET/POST /v1/practice/attendance`. Staff can select a saved practice and roster player, record participation status, available minutes, period IDs, notes, and source references, then inspect aggregate counts and limited/absent flags. The API enforces organization roster/practice linkage and preserves the medical/eligibility boundary.

Current verification correction (2026-08-25): the frontend suite now passes 85/85 tests and the Python suite passes 571/571 tests after the attendance slice; the production build and static asset/deep-link check pass.

Outcome analytics addendum (2026-08-25): the Analytics workbench now exposes separate outcome and comparison views plus a governed outcome recorder backed by `GET/POST /v1/analytics/outcomes`. Records link an intended play, practice period, game-plan decision, scouting claim, or player assignment to an observed result and evidence refs; the service preserves sample size, Wilson uncertainty, confidence, generalization eligibility, and human-review requirements. The frontend suite now passes 86/86 tests and the Python suite passes 576/576 tests after this slice; the production build passes.

Film workflow-link addendum (2026-08-25): Film observations now persist normalized `linked_record_refs` for `playbook`, `scouting`, `player_development`, `game_plan`, and `analytics` targets. The Film Studio authoring controls accept governed `type:id` references for telestration, tracking, and evidence tags; the inspector renders one-click workspace links, and Scouting, Player, Game Plan, and Analytics honor the record query to open the requested context. The Film Studio panel is lazy-loaded so the Film route remains 19.61 KiB and the complete local suite now passes 89/89 frontend and 578/578 Python tests.

Practice outcome addendum (2026-08-25): the Practice workbench now has a lazy-loaded Rep outcomes view. Staff select a saved practice period and record observed result, successful reps, observed sample, practice/play/drill context, optional Film observation IDs, and coaching notes. The recorder submits an organization-scoped `practice_period` outcome to `POST /v1/analytics/outcomes`, preserving the practice and period lineage while keeping activation and player-status changes outside the workflow. The main Practice route remains 28.25 KiB with a 4.98 KiB recorder chunk; the current local suite passes 89/89 frontend and 579/579 Python tests.

Scouting tendency addendum (2026-08-25): the Scouting workbench now queries `GET /v1/scouting/tendency-explorer` when the Explorer tab is active. The organization-scoped service normalizes down, distance, field zone, personnel, formation, motion, front, coverage, and pressure dimensions; groups claims with sample/confidence context; preserves source clips/evidence; detects explicit and stance-derived contradictions; and returns explainable low-sample, missing-evidence, low-confidence, contradiction, and staff-review gates. The React explorer retains its local interaction fallback if the server query is unavailable, and existing collaboration handoff keeps game-plan claims under human review. The Scouting route is 20.59 KiB; the current local suite passes 90/90 frontend and 583/583 Python tests.

## Remaining migration order

1. Close the explicit advanced Play Designer parity boundary above.
2. Expand provider-managed/range-efficient media playback and deeper media-to-play linking; local playback, telestration, tracking, voice notes, and governed downstream Film links are implemented.
3. Add richer canonical drill and position-group selectors to Practice and Player authoring; the Roster and Playbook selectors are now connected in Practice.
4. Complete true multi-user edit convergence and advanced publishing/layout composition where required; revision-aware handoff, cursor presence, offline outbox, and visual version/merge comparison are now available.
5. Run cross-browser visual baselines, screen-reader/contrast automation, large-library performance traces, and moderated role-based usability validation.
6. Complete the formal feature-parity audit and make a separately authorized legacy-dashboard retirement decision.

Defensive authoring and route-budget correction (2026-08-27): the assignment
inspector now provides structured defensive fit, coverage, pressure, stunt, and
rotation presets, while the Play Designer route entry lazy-loads its heavy
canvas, palette, toolbar, inspector, timeline, teaching, export, and tutorial
modules. Verification is 137/137 frontend tests across 33 files, 593/593
Python regression tests, passing typecheck/build, and a 45.18 KiB Play Designer
route entry under the 90 KiB HTTP budget. Production deployment, cross-browser
pilot evidence, and owner authorization remain separate gates.

Geometry semantics addendum (2026-08-27): the Play Designer now labels
start/stem/break/finish handles for keyboard and pointer authoring, provides
unit-aware angle presets, and marks timed intersecting routes with accessible
possible-collision feedback. Verification remains 137/137 frontend tests,
593/593 Python tests, passing typecheck/build, and a 45.18 KiB designer route
entry under the 90 KiB budget.

Defensive exchange addendum (2026-08-27): defensive rush, stunt, and rotation
assignments can be linked as reciprocal relationships. Partner selection updates
both assignments and the exchange-role selector records the paired semantic
relationship for timeline, teaching, validation, review, and export workflows.
Verification now passes 163/163 frontend tests across 42 files, 597/597 Python
tests, passing typecheck/build, and a 45.88 KiB designer route entry.

Governed legality approval addendum (2026-08-28): the React Play Designer
Checks panel now lets authorized staff submit an override request for an
overrideable finding with rationale, decision reference, evidence references,
and an expiry. Pending requests are rendered in an owner-approval queue, and
program owners can approve them with a separate approval decision reference.
The server remains authoritative for role, organization, finding, state, and
expiry enforcement; approval does not publish a play. Verification passes
238/238 frontend tests across 49 files, 634/634 Python tests, typecheck, the
production frontend build, and `git diff --check`. Stage 0 owner approval,
production deployment, real-data integration, and moderated pilot evidence
remain pending.

Professional asset catalog addendum (2026-08-28): the canonical Play Designer
registry now contains 128 validated assets across formations, routes, motions,
runs, protections, blocks, fronts, coverages, pressures, stunts, rotations,
checks, and teaching annotations. The additions include pressure, coverage,
motion, key-read, communication, error-correction, and synchronized teaching
pause cues, plus wheel, whip, choice, glance, leak, screen-release, duo,
power, counter, pin-pull, sweep, man, half-slide, empty, play-action, and
sprint-out offensive variations. Registry validation confirms unique IDs and terms, required
accessibility metadata, lifecycle metadata, and replacement safety. The
existing palette, compatibility scoring, alias search, lifecycle filtering,
thumbnails, templates, and position toolkit consume the same registry.

Concept template addendum (2026-08-28): the reusable system template catalog now
contains 11 approved concept/protection/coverage/pressure templates. The new
templates add Empty Quick Choice, Counter GT, and TEX / ET Exchange with
assignments, partner-aware exchange fields, timing markers, coaching points,
situation tags, and companion-layer metadata. Template loading and materializer
tests confirm these entries are available to the organization-scoped editor;
organization-specific templates remain separately persisted and governed.

Local runtime readiness addendum (2026-08-28): a browser smoke pass against the
running local application verified Film Room rendering, Playbook routing, and
the protected Play Designer organization-session boundary with no console
errors. A second readiness pass using disposable local-only authentication and
observability configuration reported `ready`: database integrity and
migrations, the 97-evaluation suite, security posture, Play Designer quality,
monitoring registration, and scheduler bounds all passed. The pass did not
contact providers, enable production, record approval, or change external
state. The unconfigured-environment result remains intentionally blocked until
runtime values are supplied, while provider deployment and production browser
validation remain external gates.

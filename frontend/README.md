# NFL FIDOS React frontend

This directory contains the incremental React and TypeScript replacement for the legacy single-page operator dashboard. The Python API and football-domain services remain authoritative.

## Current verification correction (2026-08-28)

The current checkout passes 199/199 frontend tests and 626/626 Python regression tests. TypeScript typecheck and the production frontend build pass. Older dated verification paragraphs below are preserved as historical records; use this correction for the current baseline.

## Current routes

- `/app` — redesigned, organization-aware Today command center.
- `/app/playbook` — visual play library backed by canonical Play Designer records.
- `/app/playbook/designer/:designId` — dedicated full-screen authoring workspace with an eight-step, completion-aware and restartable in-app tutorial; use `/new`, optionally with a template query, to start a design.
- `/app/inbox` — unified operations queue for reviews, due work, blockers, ownership, unread notifications, and safe deep links.
- `/app/roster` — organization-scoped player registry, depth charts, personnel packages, availability, and privacy-filtered player access.
- `/app/analytics` — outcome observations, lineage, uncertainty, design-to-outcome comparison, and staff-ready reporting.
- `/app/delivery` — game-week agenda, task ownership/completion, packet checklist, release readiness, and delivery boundaries.
- `/app/collaboration` — organization-scoped cross-system threads, mentions, assignments, due dates, notifications, activity, and expiring staff presence.
- `/app/film` — film assets, clips, observations, playlists, annotation sessions, voice notes, frame-linked player tracking, and evidence-aware authoring.
- `/app/practice` — saved plans, period timelines, live Roster/Playbook/Drill-linked period assignments, load findings, minute/rep envelopes, and period-plan authoring.
- `/app/scouting` — opponent profiles, reports, matchups, evolution, evidence trails, and human-reviewed report composition.
- `/app/game-plan` — weekly plan inspection, situational/counter matrices, evidence, staff decision threads with replies/resolution, and the owner-gated Release Room with dependency manifests and unresolved-reference visibility.
- `/app/player` — privacy-scoped assignments, lessons, read reveal, mastery, development plans, quiz history, coach assignment controls, and privacy-scoped offline cache fallback.
- `/app/admin` — organization context, source registry, Stage 0 evidence boundaries, pilot readiness, and canonical approval controls.
- `/app/reviews` — governed review queue with evidence inspection, return/reject decisions, and approval only through supported canonical workflows.
- `/operator-dashboard` — preserved legacy interface.

## Local development

Run the Python API on port 8080, then use a second PowerShell terminal:

```powershell
cd frontend
npm install
npm run dev
```

Vite serves the frontend on `http://127.0.0.1:5173/app/` and proxies `/health` and `/v1` to the Python server.

## Production-style local build

```powershell
cd frontend
npm test
npm run build
cd ..
$env:PYTHONPATH = (Resolve-Path '.\src').Path
python -m nfl_fidos.server
```

The Python server serves the built SPA at `http://127.0.0.1:8080/app`. Deep links use an index fallback; hashed assets use immutable caching. The Play Designer is a lazy route chunk so loading Today or Playbook does not download the editor implementation. The Docker build compiles the frontend in a dedicated Node stage.

## Architecture boundaries

- Organization tokens are kept in `sessionStorage`, never bundled or written to long-lived browser storage.
- The API remains the authority for roles, organization scope, validation, approval, publishing, collaboration, and exports.
- React Query deduplicates and caches API reads without copying canonical server records into browser persistence.
- Independent workspace reads are fetched in parallel, and each operational page ships as its own lazy route bundle.
- The shared operational workbench provides accessible tabs, search, loading/error/disconnected states, record inspection, mutation feedback, and responsive desktop/tablet layouts without fabricating UI-only records.
- The Play Designer keeps bounded undo/redo state in memory, autosaves canonical revisions through the API, consumes the authenticated bounded collaboration stream with reconnecting invalidation, and requires an explicit server-load or local-copy choice for revision conflicts.
- Football diagrams are generated from canonical player and path coordinates; cards and the editor do not use fabricated thumbnails.
- The design system lives in `src/styles/tokens.css`, with reusable shell, status, metric, play-card, field-thumbnail, dialog, empty-state, page-header, description-box, workspace-feature, and full-screen designer components.
- Every migrated page has a visible purpose description. Every operational workspace exposes feature-level purpose, operation, inputs, outputs, status, workflow, and authority boundaries. Play Designer adds contextual descriptions for its asset library, field, timeline, inspector tabs, validation, and review systems.
- The Play Designer tutorial opens for a first-time browser profile, never edits the play, can be dismissed at any point, records completion only after Finish, and can always be restarted from the toolbar help control.
- Geometry and editor-history transitions are pure modules with direct unit coverage.

Player, roster, analytics, delivery, scouting, and release authoring now uses organization-scoped roster targets and source-linked catalog pickers for Playbook, Film, Practice, Depth Chart, Personnel Package, Outcome Report, release, practice, packet, film-evidence, and game-plan evidence records, while preserving manual IDs for approved records that are not yet in the catalog.

Admin governance now exposes non-activating pilot readiness, bounded organization selection, pilot delivery-package composition, and usability/accessibility evidence submission through the canonical Python API. The dedicated `/app/admin/stage-25` route exposes compiled-specification inspection, acceptance history, and program-owner-only acceptance evidence without activating production or advancing the stage. The dedicated `/app/admin/population-readiness` route exposes the 13-component organization operating-bundle matrix, season selection, explicit blockers, and read-only activation boundaries.

## Quality commands

```powershell
npm run typecheck
npm test
npm run build
```

Python HTTP integration tests additionally verify legacy CSS/JavaScript delivery, UTF-8 MIME types, every React workspace deep link, the lazy Play Designer and operational-page assets, content security policy, immutable caching, and local bundle-size budgets. See `../runbooks/frontend-migration.md` and `../runbooks/play-designer-tutorial.md` for the tested capability, tutorial, and parity boundaries.

Current local verification (2026-08-28): 252/252 frontend tests across 49 files and 653/653 Python regression tests pass, the production build and TypeScript typecheck compile successfully, each migrated operational route bundle remains under the local 30 KiB budget, and the served entry stylesheet remains under the enforced 90 KiB HTTP budget. Authenticated route/deep-link plus seeded organization checks pass. Play Designer also exposes the server-backed role-filtered teaching/player view with progressive step reveal, accessible read-through, quizzes, mastery recording, practice linkage, encrypted offline draft recovery, revision-aware remote edit handoff with field-level three-way merging for disjoint local/server edits, and layout-aware multi-play packet export with paginated call-sheet, wristband-grid, and play-card grid composition; Player Learning Hub offline approved-content caching is encrypted and session-bound; the Collaboration Hub receives organization-scoped replayable live events with role visibility filtering, shared staff cursor overlays, and an encrypted offline mutation outbox with reconnect delivery; Practice period authoring now offers catalog-backed multi-select position groups derived from roster and drill data while preserving custom player/group entry, Practice Attendance now records roster-linked participation, available minutes, period linkage, source notes, and human-review flags, and Practice Rep Outcomes now records period-specific successes/samples and linked play/drill/film evidence into Analytics; Analytics now captures intended-versus-actual outcomes with linked play/practice/film/game-plan evidence, sample-size-aware confidence, Wilson uncertainty, and review-required flags; Film now supports approved server-path asset registration with source-root validation, file hashing, provenance before clip creation, bounded authenticated `index` jobs that persist searchable stream metadata, and governed one-click evidence links from Film observations to Playbook, Scouting, Player Development, Game Plan, and Analytics records; Scouting Tendency Explorer now queries an authoritative organization-scoped endpoint while preserving dimension filters, trends, explicit and stance-derived contradictions, source clips/evidence, sample/confidence context, and explainable review gates before routing game-plan review requests through collaboration; Game Plan Release Room provides frozen source-plan field comparison with added, removed, and changed classifications before approval; Delivery Center exposes five-audience packet readiness with linked prerequisites and blockers plus reviewable packet assembly, automatically creates an internal unread owner notification for new game-week responsibilities, and routes packet/task blockers into the role-aware Operations Inbox; Admin loads persisted pilot selections, delivery packages, and usability/accessibility findings for inspection alongside readiness reports; Stage 25 now has a dedicated compiled-specification acceptance route with owner-only evidence submission and explicit non-activation controls; population readiness now has a dedicated 13-component organization matrix route with season-aware blockers and read-only safety controls.

Play Designer verification addendum (2026-08-25): the current frontend suite passes 116 tests across 27 files, the focused Play Designer service/API/export suite passes 23 tests, TypeScript typecheck passes, and the production build passes with the Play Designer route chunk at 89.48 kB under the local 90 kB designer ceiling. The designer now includes organization-backed offense/defense concept templates, pre-snap timeline normalization, immutable visual version overlays, and filtered role/position-group teaching diagrams with progressive reveal and replay. Remaining work is explicitly tracked in `PLAY_DESIGNER_COMPETITIVE_BENCHMARK.md`; this local evidence does not constitute production deployment, moderated pilot completion, or Stage 0 owner authorization.

Export verification addendum (2026-08-25): generated Play Designer artifacts now carry a source manifest and manifest hash, and signed exports cover that hash. The export dialog displays each source play, version, immutable snapshot, approval/release state, and source-lock hash before download.

Audience export addendum (2026-08-25): the same export flow now accepts coach/full-call, player, or position-group audience selection and sends the selected role through the organization-scoped API for focused artifacts.

Wristband layout addendum (2026-08-25): server-rendered wristband PDFs now support standard two-column, compact three-column, and four-column sideline-strip layouts with layout-specific capacity and typography, plus validation that prevents wristband layouts from being used on unrelated artifact kinds.

Export preflight addendum (2026-08-26): the export dialog now calls the organization-scoped non-rendering `/v1/playbook/designs/export/preflight` endpoint before allowing artifact generation. The check validates the selected designs, audience role, format, and effective layout; shows warning/error paths and the source-lock hash; and expires automatically when any export input changes. A successful preflight is required before the signed, server-rendered artifact can be generated. Verification: 117 frontend tests across 27 files, focused Play Designer backend checks 26/26, typecheck, and production build pass.

Install handout addendum (2026-08-26): PDF install-sheet exports use a dedicated coaching layout with a field diagram, canonical assignment ledger, ownership labels, landmark/timing cues, teaching notes, branding, role filtering, and black-and-white support. CSV install output remains available for structured integrations.

Position authoring addendum (2026-08-26): selecting a player icon in Play Designer now exposes a ranked position toolkit backed by the asset registry and template library. Position profiles provide role-specific route, motion, run, block/protection, coverage, rush, stunt, fit, read, check, and teaching options with descriptions and timing guides; asset selection activates the existing drawing tool, and suggested concept layers insert through the canonical template materializer. Verification: 125 frontend tests across 30 files, TypeScript typecheck, and production build pass.

Visual authoring addendum (2026-08-26): selected assignments support explicit arrow/line meaning, end/start/both/none arrowheads, smooth versus sharp path geometry, solid/dashed/dotted treatment, line weight, and line-cap controls. The SVG field renders those persisted choices while preserving path animation and accessible assignment selection. Verification: 125 frontend tests across 30 files, TypeScript typecheck, and production build pass.

Action materialization addendum (2026-08-26): each ranked position option now has a one-click starting-action control. It generates editable player-owned geometry with asset linkage, route/run/block/coverage semantics, landmarks, depth, teaching metadata, and synchronized timing; motions begin on the pre-snap timeline. Manual draw remains available as a separate action.

Geometry authoring addendum (2026-08-26): assignment endpoints can snap to hashes, line of scrimmage, five-, ten-, and fifteen-yard landmarks, or the goal line. Editing Depth (yards) updates the actual endpoint with unit-aware offensive/defensive direction while preserving other handles. The feature is covered by geometry and inspector tests.

Defensive authoring addendum (2026-08-27): defensive assignments now expose a
grouped responsibility-preset selector for fit, coverage, pressure, stunt, and
rotation starters. It covers spill/box/force/cutback fits, deep-third/
quarter-match/hook-curl/robber/man-trail/bracket coverage, edge and A-gap
pressure, TEX/ET stunts, and sky/spin rotations. Presets populate editable
coach-readable fields for gap, fit rule, zone, coverage, rush lane, stunt or
rotation, objective, responsibility, leverage, phase, and arrow meaning; they
remain authoring aids and do not bypass server legality checks. Verification:
137 frontend tests across 33 files, TypeScript typecheck, and production build
pass.

Release verification correction (2026-08-27): the full frontend suite passes
163/163 across 42 files, the Play Designer production route entry is 45.88 KiB
after lazy-loading the canvas, palette, toolbar, inspector, timeline, teaching,
export, and tutorial modules, the production build and TypeScript typecheck
pass, and the full Python regression suite passes 597/597. The HTTP static
asset/deep-link and designer route-size checks are green. This local evidence
does not close target-environment deployment, moderated pilot, or owner-
approval gates.

Geometry semantics addendum (2026-08-27): assignment inspection now provides
unit-aware break-angle presets and the canvas identifies start, stem, break,
and finish handles for keyboard and pointer authoring. Timed intersecting
routes receive accessible possible-collision feedback on the field. These
geometry updates remain canonical element mutations and continue through undo,
sync, validation, versioning, and export.

Defensive exchange addendum (2026-08-27): defensive rush, stunt, and rotation
assignments can be linked as reciprocal relationships. Partner selection updates
both assignments, while explicit roles describe penetrate/loop, rush/replace,
drop/replace, carry/transfer, and rotate/replace behavior for the timeline,
teaching, validation, review, and export consumers. Verification: 137 frontend
tests across 33 files, typecheck, and production build pass.

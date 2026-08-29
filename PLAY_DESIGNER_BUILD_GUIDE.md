# NFL FIDOS Professional Play Designer

## Purpose

This document is the implementation blueprint for building the interactive
playbook designer inside the NFL FIDOS application. It defines what the
product must do, what assets must exist, how play data must be stored, how the
editor should behave, how football correctness is checked, and how a finished
play becomes a teaching, practice, game-plan, print, or call-sheet artifact.

The play designer is a workspace inside NFL FIDOS, not a disconnected drawing
utility. It must use the same organization, permissions, terminology, source,
approval, game-plan, practice, analytics, and audit systems as the rest of the
application.

## 1. Pre-build audit and improvements

### 1.1 What already exists

The repository already contains a dashboard shell, play-record and visual-play
contracts, a notation standard, play-family corpus, compiler, role-based views,
organization terminology contracts, scheme models, playbook authoring request
contracts, and a new structured play-design validator. These are the foundation
for the editor and should be extended rather than bypassed.

Relevant existing files:

- `ui/operator-dashboard.html` — current application shell and workspace host
- `visual/notation-standard.json` — current visual semantics and view contract
- `contracts/play-record.schema.json` — canonical minimum play record
- `contracts/visual-play.schema.json` — renderable visual-play contract
- `contracts/playbook-authoring.schema.json` — authoring envelope
- `contracts/playbook-view.schema.json` — role-view contract
- `contracts/scheme-model.schema.json` — compositional scheme contract
- `src/nfl_fidos/play_compiler.py` — minimum structural compiler
- `src/nfl_fidos/playbook_architecture.py` — families, approval, role extraction
- `src/nfl_fidos/play_creation.py` — structured design validation foundation

### 1.2 Improvements required before calling the feature professional

The previous feature list was directionally correct but incomplete. These
improvements are required to make the result production-grade:

1. **Use one canonical model.** The diagram, assignment table, animation,
   role card, export, and AI explanation must all render from the same versioned
   play-design record. Never store the diagram as an unrelated image.
2. **Separate normalized football terms from team language.** Store `post`,
   `cover_3`, and `jet` as normalized IDs while allowing each organization to
   display its own aliases, pronunciation, call word, wristband code, and
   coaching definition.
3. **Make rules configurable by competition.** NFL, NCAA, high school, youth,
   and flag rules differ. The editor needs a rule profile and must label every
   warning with the profile that produced it.
4. **Model time, not only geometry.** Routes, blocks, rushes, motion, reads,
   protection, and coverage need snap-relative timing and phase markers.
5. **Treat offense and defense as independent layers.** A play should support
   offense only, defense only, or an offense-versus-defense matchup with a
   canonical overlay and isolated what-if variants.
6. **Support teaching views.** A coordinator needs the whole picture; a player
   needs only the player's alignment, motion, assignment, landmark, key, and
   coaching points.
7. **Add a first-class legality and completeness linter.** Warnings must be
   explainable, actionable, dismissible with a reason, and rechecked whenever a
   formation, motion, assignment, or rule profile changes.
8. **Build for touch and keyboard use.** Tablet sideline use is a primary mode,
   not a smaller desktop. Every canvas action needs a keyboard and accessible
   text alternative.
9. **Make revisions safe.** Version history, compare, duplicate-as-variant,
   approval locks, and immutable published versions are mandatory.
10. **Design outputs before the editor.** A good design must produce a clean
    coaching card, install sheet, player card, wristband/call sheet, PDF,
    accessible text, and machine-readable export.
11. **Add rehearsal and install linkage.** Plays should connect to practice
    scripts, drills, install days, opponent notes, film clips, and mastery
    checks without copying data manually.
12. **Keep provenance visible.** Every imported, AI-suggested, copied, or
    manually authored element needs source, author, timestamp, version, and
    approval history.
13. **Plan for collaboration.** Staff comments, review threads, presence,
    conflict handling, and role-based edit permissions are needed before
    multiple coaches use the same playbook.
14. **Use asset tokens, not arbitrary colors.** Color must communicate meaning
    and have line-style/label fallbacks for printing, color blindness, and dark
    mode.
15. **Test football semantics and rendering separately.** A diagram can look
    correct while assignments are wrong, and a correct model can render badly.

## 2. Product architecture

```text
NFL FIDOS Application
├── Playbook workspace
│   ├── Library: plays, families, formations, concepts, schemes
│   ├── Create/edit: interactive designer
│   ├── Review: lint, comments, compare, approvals
│   ├── Teach: role cards, install pages, quizzes, animation
│   └── Export: PDF, print, wristband, call sheet, JSON, image
├── Organization context and terminology
├── Roster and personnel
├── Practice/install planner
├── Game plan and opponent context
├── Film and analytics links
└── Governance, permissions, provenance, audit, deployment controls
```

The editor should be a routed application workspace, for example:

`/playbook` → library

`/playbook/new` → template wizard

`/playbook/:playId/edit` → interactive designer

`/playbook/:playId/review` → validation and staff review

`/playbook/:playId/teach/:role` → player/position view

`/playbook/:playId/export` → output builder

The UI may begin as a dashboard-integrated module, but the editor should be
implemented as a componentized client workspace with a stable API boundary so
the current single-page dashboard can later be replaced without changing the
football model.

## 3. Canonical data model

### 3.1 Play-design envelope

Every design requires:

- design ID and semantic version
- organization/team scope
- unit: offense, defense, or special teams
- competition/rule profile
- play family, concept, scheme, and call language
- personnel package and formation/front
- players and starting coordinates
- elements and assignments
- snap-relative timeline
- situation tags
- source/provenance
- validation results
- approval/publishing state

### 3.2 Player model

Each player object should include:

- stable player ID and display label
- position and role alias, such as `X`, `Z`, `F`, `Y`, `H`, `QB`, `RB`
- roster/player reference when known
- side and unit
- start coordinate, stance, orientation, and depth
- eligibility and alignment status
- position-group ownership
- role-view visibility
- optional motion participant flag

### 3.3 Element model

Elements are typed, versioned instructions attached to a player or group:

- `route`
- `motion`
- `run`
- `block`
- `protection`
- `read`
- `coverage`
- `rush`
- `fit`
- `stunt`
- `rotation`
- `assignment_note`
- `check`
- `ball_path`
- `landmark`

Each movement element should support start point, path points, endpoint,
direction, depth, timing, arrow style, label, coach notes, and conditions.

### 3.4 Offensive assignment fields

The editor must support explicit structured values for:

- formation and alignment
- release/stem
- route family and route variation
- depth and landmark
- break angle and leverage
- tempo and settle rule
- primary, secondary, alert, hot, and checkdown read
- conflict defender and coverage key
- ball location/target
- run track and aiming point
- blocking rule, gap, target, combo, pull, trap, or climb
- pass-protection responsibility, slide, scan, and release condition
- motion, fake, mesh, exchange, or RPO constraint

### 3.5 Defensive assignment fields

The editor must support:

- package and personnel
- front, shade, technique, and alignment depth
- gap, fit, force, spill, contain, scrape, and cutback responsibility
- rush lane, aiming point, stunt partner, and exchange order
- man assignment, zone landmark, match rule, bracket, or banjo rule
- leverage, press/off, safety shell, rotation, and disguise
- motion adjustment, communication, check, and alert
- spy, green-dog, simulated-pressure, drop, or replacement assignment

### 3.6 Conditions and variants

Assignments must support conditions such as:

- versus front or coverage
- if defender blitzes
- if motion is followed
- if back releases
- if formation strength changes
- field/boundary/hash
- down, distance, red zone, backed up, goal line, two-minute, or third down
- personnel substitution or injury contingency

Variants should reference the parent design and record only the changed
components. This keeps the play family searchable and makes comparisons useful.

## 4. Asset library specification

The asset library is the set of reusable building blocks shown in the editor's
palette. Assets are parametric records, not flat screenshots.

### 4.1 Formation assets

Offensive formation templates must include:

- single-back, I, pistol, shotgun, empty, split-back, ace, wing, bunch,
  stack, twins, 2x2, 3x1, trips, quads, nub, condensed, unbalanced, and
  goal-line families
- player slots, splits, depth, strength, eligible/ineligible assumptions,
  default labels, and mirrored versions
- motion-compatible slots and shift behavior
- personnel compatibility and rule-profile warnings

Defensive formation/front templates must include:

- 3-4, 4-3, 4-2-5, 3-3-5, 4-4, bear, tite, odd, even, nickel, dime, goal line,
  and sub-package families
- techniques, shades, box count, shell, default gap fits, and pressure slots
- mirrored/field-boundary variants
- disguise and rotation states

### 4.2 Offensive route assets

Provide canonical route assets for:

- go/vertical, fade, seam, post, skinny post, corner, deep out, speed out,
  comeback, curl, dig, glance, slant, drag, shallow, deep over, whip, pivot,
  choice, option, wheel, angle, Texas, flat, arrow, swing, screen, return,
  stop, settle, burst, and scramble rules

Each route asset needs adjustable handles for release, stem, depth, break,
landmark, width, leverage, and endpoint. It also needs a short definition,
coaching points, common tags, timing defaults, and a text equivalent.

### 4.3 Run and blocking assets

Include inside zone, outside zone, split zone, duo, power, counter, dart,
trap, draw, sweep, toss, pin-pull, QB run, read-option, RPO, screen, and
play-action families.

Blocking assets must support base, reach, drive, down, gap, combo, climb, pull,
kick, wrap, sift, insert, arc, seal, crack, stalk, screen-release, slide
protection, full-slide, half-slide, man protection, scan, and check-release.

### 4.4 Motion and shift assets

Provide jet, fly, orbit, return, zip, yo-yo, short, fast, trade, shift, reset,
and return-motion assets. Each requires start/end slot, path, speed, pre-snap
phase, reset requirement, snap relationship, and legality metadata.

### 4.5 Defensive assets

Front assets: over, under, even, odd, bear, tite, mint, wide, reduced, nickel,
dime, goal-line, and custom front packages.

Coverage assets: Cover 0, Cover 1, Cover 2, Tampa 2, Cover 3, match 3, Cover 4,
quarters, Cover 6, man, match-man, bracket, banjo, robber, lurk, and prevent.

Pressure assets: edge, interior, cross-dog, mug, fire zone, overload, creeper,
simulated pressure, green dog, spy, contain, and replacement rushes.

Line-game assets: TEX, ET, TE, twist, pirate, long-stick, pinch, slant, loop,
exchange, and stunt combinations.

### 4.6 Annotation and teaching assets

- coaching point
- read number
- conflict defender
- landmark
- aiming point
- alert/check diamond
- motion cue
- cadence cue
- opponent tendency note
- “why it works” callout
- “if/then” adjustment card
- install tag and mastery check

### 4.7 Asset metadata

Every asset requires:

- stable asset ID and version
- unit and position group
- normalized term and organization aliases
- thumbnail and full render definition
- editable parameters
- compatible formations/personnel/rule profiles
- accessibility description
- author/source/license
- coaching definition and examples
- approval state
- deprecation/replacement link

## 5. Notation and rendering system

The renderer must use the existing notation standard as the single visual
source of truth.

Minimum semantic rules:

- solid route arrow: receiver route
- dashed motion arrow: pre-snap motion
- solid run arrow: ball carrier path
- blocking bar/short line: block direction or target
- red pressure arrow: blitz/rush path
- dashed coverage arc/zone boundary: coverage responsibility
- numbered marker: read progression
- diamond: check, alert, or adjustment
- distinct player marker: player/position identity
- ball icon: snap/ball location
- line of scrimmage, hash, sidelines, end zone, and optional first-down line

Every visual element must have a semantic text equivalent. Color is never the
only way to distinguish a route, rush, coverage, or warning.

The renderer must support:

- responsive scaling without changing football geometry
- high-contrast and grayscale output
- dark mode
- print-safe line weights
- selection/focus states
- layer visibility
- animation interpolation
- export at predictable dimensions
- deterministic rendering for snapshot tests

## 6. Interactive editor UX

### 6.1 Workspace layout

Desktop layout:

- left: asset palette and search
- center: field canvas
- right: selected-player/element inspector
- bottom: timeline, animation, validation, and history tabs
- top: breadcrumb, play name, status, save, review, compare, export

Tablet layout:

- collapsible asset drawer
- full-width canvas
- bottom sheet inspector
- persistent save/undo/redo and validation indicators

Mobile layout:

- read/teach mode first
- simplified edit mode for labels, assignments, and notes
- full drawing reserved for tablet/desktop unless explicitly enabled

### 6.2 Creation flow

1. Choose unit: offense, defense, special teams, or matchup.
2. Choose a template or start blank.
3. Select rule profile, organization, personnel, and situation.
4. Choose formation/front and mirror/field orientation.
5. Confirm player slots and roster labels.
6. Add routes, runs, blocks, reads, coverage, rushes, and annotations.
7. Add motion, shifts, checks, and conditional adjustments.
8. Set snap-relative timing and animate the design.
9. Resolve validator issues.
10. Add coaching notes, opponent notes, and install dependencies.
11. Save draft, request staff review, or publish an approved version.

### 6.3 Canvas interactions

- drag assets onto player slots
- click a player to select the player and all attached elements
- drag path handles and landmarks
- snap to hashes, yard lines, numbers, landmarks, and alignment guides
- draw freeform path, then classify or leave as custom
- mirror a design while preserving role semantics
- multi-select and group elements
- lock layers or individual assignments
- duplicate as a situational variant
- hide defense, offense, annotations, or coaching overlays
- scrub the timeline and play/pause animation
- keyboard shortcuts for select, duplicate, undo, redo, delete, mirror, zoom,
  and layer visibility

### 6.4 Inspector behavior

The inspector should show only fields relevant to the selected object, while
also exposing advanced fields for coordinators. It must provide:

- normalized term and organization call word
- assignment/responsibility
- timing and landmarks
- conditions and variants
- coaching points
- validator messages
- provenance and last edit
- visibility by role/view

## 7. Validation and football linting

Validation has four layers:

### 7.1 Schema validation

Check required fields, types, IDs, references, coordinates, versions, and
organization scope.

### 7.2 Structural validation

Check player count, duplicate roles, missing assignments, missing paths,
orphaned elements, invalid arrow styles, impossible timeline values, and
unresolved assets.

### 7.3 Rule-profile validation

Check formation eligibility, player alignment, motion direction/reset, snap
state, substitutions, and profile-specific rules. Every message must say which
rule profile produced it.

### 7.4 Football completeness validation

Check that every player has a responsibility, every route has a landmark or
custom explanation, every pass play has a read/checkdown/protection model,
every run has a track and blocking rule, and every defense has a front, fit,
rush/contain plan, and coverage responsibility.

Example severities:

- error: cannot validate or publish
- warning: coach decision required
- info: teaching or optimization suggestion
- dismissed: retained with reason and reviewer

## 8. Library, search, and reuse

The library must support:

- play, family, concept, formation, route, front, coverage, and asset views
- filters for unit, personnel, situation, field zone, down/distance, opponent,
  install level, approval, and owner
- full-text search across normalized terms, aliases, notes, and assignments
- “show every play using this route/motion/coverage”
- compare two versions or two variants
- duplicate, mirror, archive, restore, and deprecate
- dependency graph showing which installs, practices, game plans, and exports
  use a play
- favorite/recent/pinned views
- organization-level asset governance

## 9. Workflow and permissions

Suggested lifecycle:

`draft → linted → staff_review → approved → game_ready → archived/superseded`

Roles:

- owner: organization-wide governance and publishing
- coordinator: author, edit, approve within assigned unit
- position coach: author/review position assignments
- analyst: annotate, link film/data, propose changes
- player: read/teach access only
- observer: read-only

Approval locks the exact version used in a game plan. Editing creates a new
version. No published game artifact should silently change because a draft was
edited later.

## 10. Outputs and integrations

Required outputs:

- full coordinator diagram
- offense-only and defense-only diagram
- player/position card
- install sheet with coaching points
- animated teaching view
- practice script reference
- call sheet
- wristband card
- printable PDF, grayscale PDF, PNG/SVG, accessible HTML/text, and JSON

Integrations should reference existing records rather than duplicate them:

- roster and depth chart
- organization terminology
- opponent profile and scouting package
- game plan and situation tags
- practice plan and drill validation
- film clips and analytics observations
- staff review threads
- mastery records and player quizzes

## 11. Technical implementation sequence

### Phase A — contracts and vocabulary

- reconcile `play-design`, `visual-play`, `play-record`, `scheme`, and
  `playbook-view` contracts
- create versioned enums for routes, motions, blocking, fronts, coverages,
  pressures, arrows, and rule profiles
- add organization alias and pronunciation fields
- define stable migration/version policy

### Phase B — asset registry

- create asset storage and CRUD API
- seed formation, route, motion, block, front, coverage, rush, and annotation
  assets
- add search, tags, compatibility rules, thumbnails, and accessibility text
- implement asset approval/deprecation workflow

### Phase C — editor shell

- add routed Playbook workspace to the dashboard
- implement field coordinate system, pan/zoom, layers, selection, and snapping
- implement player placement and formation templates
- implement undo/redo and autosave draft behavior

### Phase D — football authoring tools

- route/run/block/protection tools
- motion/shift tool
- read/check/annotation tool
- defense front/fit/coverage/rush/stunt/rotation tools
- inspector panels and role-based assignment forms

### Phase E — timeline and renderers

- snap-relative timeline
- deterministic animation
- coach/QB/position/player/print views
- accessible text renderer
- image/PDF/wristband/call-sheet exports

### Phase F — validation and workflows

- schema and reference validation
- rule-profile legality checks
- football completeness checks
- review/comments/approval/lock/version compare
- game-plan, practice, film, and mastery links

### Phase G — hardening and pilot

- browser compatibility and tablet testing
- performance tests with large libraries
- keyboard/screen-reader/color-blind testing
- security and organization-isolation testing
- staff usability pilot with reversible local data
- evidence packet and Stage 0/production authorization review

## 12. Testing strategy

Unit tests must cover vocabulary normalization, coordinate math, route handles,
mirroring, timing, path classification, role extraction, variants, validator
rules, permissions, versioning, and export naming.

Contract tests must verify every saved design validates against the schema and
renders into every required view.

Visual regression tests must cover formation templates, route styles, defensive
layers, high contrast, grayscale, mobile, print, and animation keyframes.

Interaction tests must cover drag/drop, touch handles, keyboard shortcuts,
undo/redo, autosave recovery, concurrent edits, and failed network requests.

Football acceptance tests should include:

- 2x2 spacing concept with motion and QB progression
- trips flood with protection and checkdown
- inside zone with combo blocks and RPO constraint
- empty formation with hot rules
- 4-2-5 Cover 3 with fits and pressure tag
- simulated pressure with a dropping rusher
- man pressure with no deep safety
- stunt/twist with exchange order
- motion adjustment and coverage rotation
- mirrored field/boundary versions

## 13. Definition of done

The feature is ready for controlled pilot only when:

- a coordinator can create a play without editing JSON
- every asset is reusable, searchable, versioned, and accessible
- offense and defense can be authored independently and together
- diagrams, tables, animation, role views, and exports agree with one model
- validator issues are explainable and rule-profile-aware
- an approved version is immutable and auditable
- tablet, keyboard, screen-reader, grayscale, and print modes work
- organization data is isolated and permissions are enforced
- drafts survive reload and recover from interrupted saves
- the complete test suite and visual regression suite pass
- practice, game-plan, film, and terminology references work
- no production claim is made until Stage 0 authorization and external setup
  are actually complete

## 14. Recommended first build slice

The safest first product increment is:

1. Playbook library route inside the dashboard.
2. Formation template picker with 2x2, trips, shotgun, 4-2-5, and Cover 3.
3. Field canvas with players, line of scrimmage, hashes, pan/zoom, select,
   snap, and undo/redo.
4. Route, motion, run, block, coverage, rush, and read assets.
5. Right-side assignment inspector.
6. Basic legality/completeness lint panel.
7. Save draft and render coordinator/player views.
8. Export one clean PDF and machine-readable JSON.

This slice proves the core loop—select template, author assignments, validate,
save, teach, and export—before the team invests in advanced collaboration,
analytics, AI assistance, or a large asset catalog.

## 15. Non-goals and safety boundaries

The editor should not silently decide a team's proprietary terminology,
football doctrine, player suitability, injury status, or game call. AI may
suggest a concept, asset, label, or adjustment, but the source, rationale,
confidence, and human approval must remain visible. Production publishing,
external organization onboarding, and live game use remain subject to the
existing NFL FIDOS governance and Stage 0 approval controls.

## 16. State-of-the-art engineering additions

The following requirements upgrade the blueprint from a feature checklist to a
production engineering specification.

### 16.1 Command-based editor architecture

The editor must change a play through typed commands rather than arbitrary
component mutations. Examples include `AddPlayer`, `MovePlayer`,
`AddRoute`, `SetAssignment`, `ApplyFormation`, `MirrorDesign`,
`SetTimelineMarker`, `ResolveLintIssue`, and `PublishVersion`.

Each command must have:

- validated input and organization scope
- author and request ID
- precondition and postcondition
- reversible inverse command when possible
- deterministic result
- audit event
- optimistic concurrency/version check

This gives undo/redo, audit, autosave, collaboration, replay, test fixtures,
and migration a common foundation. The persisted design remains the current
materialized state; commands/events provide the history and evidence.

### 16.2 Offline-first and recovery behavior

The editor must remain usable during temporary connectivity loss. It should:

- save drafts locally using an encrypted browser storage layer
- show explicit offline/syncing/synced/conflict states
- queue commands and retry with bounded backoff
- recover the last stable draft after a browser crash
- never claim a server save succeeded without a server acknowledgment
- provide “download recovery package” for emergency handoff
- reconcile drafts against the last server version before publishing

Collaborative sync may use a CRDT or another deliberately selected approach,
but the football model still needs domain-level conflict rules. For example,
two users may safely move different players, while simultaneous edits to the
same assignment must create a visible review conflict rather than silently
choosing a winner. Yjs documents provide a useful reference for awareness,
offline editing, and shared updates, but the project must evaluate persistence,
authorization, auditability, and operational complexity before adoption.

### 16.3 Deterministic rendering pipeline

All views must be generated by a shared renderer with:

- canonical normalized coordinates
- stable layer ordering
- deterministic IDs and z-index rules
- font fallback and embedded export fonts
- SVG as the semantic vector representation where practical
- raster export only as a derived artifact
- render metadata containing source design/version/renderer version
- snapshot hashes for visual regression
- server-side rendering for trusted exports

Interactive SVG elements must use appropriate pointer targeting, focus states,
and text alternatives. The renderer must not rely on browser-specific CSS or
device pixel ratios for football geometry.

### 16.4 Performance budgets

Initial targets for a normal play on a supported tablet/desktop:

- first interactive editor render: under 2 seconds on the pilot reference device
- pointer/drag response: 60 fps target; never block the main thread with linting
- route or player mutation feedback: under 100 ms locally
- autosave acknowledgment indicator: under 1 second when connected
- open library search results: under 300 ms for indexed local results
- export request accepted: under 1 second, with asynchronous progress thereafter
- 100-element design and 50 visible layers without unusable interaction

Use debounced non-blocking validation, incremental rendering, memoized assets,
virtualized library lists, and background export jobs. Measure these budgets in
CI and on the pilot tablet instead of relying on developer hardware.

### 16.5 Asset governance and extensibility

Asset types must be registered through a manifest rather than hard-coded into
the palette. A manifest defines schema, renderer, editor controls, validators,
compatibility rules, migration, accessibility text, and permissions.

Asset lifecycle:

`proposed → reviewed → approved → active → deprecated → retired`

No active asset may be deleted if it is referenced by an approved play. It must
be deprecated and replaced through an explicit migration. Asset packs must be
portable between organizations only when licensing, terminology, and source
permissions allow it.

### 16.6 Versioning, branching, and merge semantics

Use immutable published versions and editable branches/drafts. A comparison
view must show:

- changed players and coordinates
- added/removed/modified paths
- assignment and terminology changes
- timing changes
- validator status changes
- source/approval changes

Branch merges must be element-aware. A merge must not flatten a newer approved
version into a draft or alter a game-plan snapshot. Every published artifact
must include the exact play version and renderer version used to create it.

### 16.7 Accessibility as an authoring-tool requirement

Target WCAG 2.2 AA for the application and the exported web/text views. The
canvas must have a synchronized structured outline where a user can navigate:

`layer → player → element → assignment → coaching note → validation message`.

Required accessibility features:

- keyboard creation and editing workflows
- visible focus and selection indicators
- no color-only meaning
- minimum contrast and scalable text
- reduced-motion mode
- screen-reader announcements for selection and validation changes
- touch targets sized for tablet use
- text/table/diagram alternatives for every play
- captions/transcript for teaching animation or audio
- error recovery without losing work

### 16.8 Security and privacy

Threat-model the editor as a repository of proprietary football strategy and
player information. Include:

- organization/tenant isolation on every read and write
- server-side authorization, not only hidden UI controls
- immutable audit events for export, share, publish, and download
- signed short-lived export links
- encryption in transit and at rest
- secret-free browser bundles
- malware/content checks for uploads
- rate limits and abuse monitoring
- retention and deletion policy for drafts, exports, and comments
- redaction rules for player health or sensitive scouting information
- explicit controls for whether data may be used for AI improvement

### 16.9 AI assistance with bounded authority

AI may assist with:

- converting a coach's plain-language idea into a draft
- suggesting compatible formations or route families
- generating player-view explanations
- detecting missing assignments or inconsistent timing
- proposing opponent-specific variants
- translating normalized terms into organization call language

AI must never directly publish, overwrite an approved play, invent a source,
assert legality without the active rule profile, or make a player-health or
game-call decision. Store prompt/input provenance, model/version, output,
confidence, citations or source links, and human disposition.

### 16.10 Observability and supportability

Instrument the editor with privacy-conscious events for:

- open/create/save/recover/export/publish failures
- lint error frequency and resolution time
- asset usage and abandoned authoring steps
- render and interaction latency
- sync conflicts and offline queue age
- authorization denials
- export rendering failures

Do not log proprietary assignment text or sensitive player data by default.
Use correlation IDs, redacted diagnostics, feature flags, kill switches, and a
support bundle that can be generated without exposing an entire organization
playbook.

## 17. State-of-the-art product improvements

### 17.1 Scenario-aware design

Add a matchup board where a coach can place an offensive concept against one or
more defensive looks, then create named answers: `base`, `versus pressure`,
`versus rotation`, `versus motion check`, and `versus scramble drill`. The
system should display what changed and why, without pretending to simulate the
opponent's actual behavior.

### 17.2 Constraint-aware authoring

When a coach moves one player or changes personnel, the editor should show
affected constraints before applying the change: eligibility, spacing,
assignment ownership, motion legality, route collision, protection conflict,
coverage gap, or timing collision. Offer fix suggestions but require the user
to accept them.

### 17.3 Teaching mode and mastery loop

Generate role-specific cards, hide other assignments, reveal reads step by
step, quiz players on alignment/assignment/key, capture confidence and errors,
and link results to practice drills and mastery records. Teaching mode must
remain faithful to the approved play version.

### 17.4 Film-to-play linkage

Allow a coach or analyst to attach film clips to a design or element: route,
front, technique, pressure, read, or correction. The film link should include
clip timestamp, source, analyst note, and whether it is an example, correction,
or opponent tendency.

### 17.5 Explainable exports

Every export should optionally include a compact “why” panel:

- objective
- primary conflict/key
- expected defensive response
- coaching points
- checks and alerts
- failure conditions
- source and approval version

This turns a diagram into a usable teaching artifact without cluttering the
primary player view.

### 17.6 Professional release management

Add release bundles for a weekly install, opponent plan, game-day call sheet,
and player package. A release bundle freezes the selected play versions,
records owner approval, generates checksums, and supports rollback to the prior
bundle.

### 17.7 Research-backed design validation

Before pilot, conduct moderated usability sessions with a coordinator,
position coach, analyst, and player. Measure time to create a standard play,
error rate, correction rate, export comprehension, and player recall. Do not
declare “good UX” from visual polish alone.

## 18. Revised delivery gates

### Gate 1 — Model integrity

All entities, references, versions, aliases, elements, timing, rule profiles,
and provenance validate. No UI work proceeds on an ambiguous model.

### Gate 2 — Authoring loop

A user can create, edit, undo, save, reload, and recover a play entirely inside
the app without editing raw JSON.

### Gate 3 — Football correctness

Canonical offensive and defensive fixtures pass structural and football
completeness validation; intentional invalid fixtures produce useful messages.

### Gate 4 — Rendering parity

Coordinator, player, print, accessible, animation, and export views agree with
the same source version and pass visual regression tests.

### Gate 5 — Collaboration and safety

Offline recovery, concurrent edits, permissions, tenant isolation, audit,
export controls, and rollback are tested under failure conditions.

### Gate 6 — Human pilot

Representative staff can complete the core workflow, understand warnings,
teach a play, and export a usable artifact with measured acceptance criteria.

### Gate 7 — Production authorization

Stage 0 owner approval, organization onboarding, deployment, secret source,
monitoring, provider integrations, and pilot authorization are independently
verified. Passing technical gates does not bypass governance.

## 19. Guide grading

The grade is based on ten categories scored from 0 to 10: football model,
authoring UX, asset library, architecture, validation, rendering/exports,
accessibility, collaboration/versioning, security/operations, and testing/
pilot readiness.

### Grade before this revision

| Category | Score | Assessment |
|---|---:|---|
| Football model | 9 | Broad offense/defense vocabulary and assignments were covered. |
| Authoring UX | 8 | Strong canvas/workflow outline, but insufficient interaction/state detail. |
| Asset library | 8 | Good inventory, but governance and extensibility were under-specified. |
| Architecture | 7 | Integration was clear, but persistence and command boundaries were missing. |
| Validation | 8 | Linting was defined, but conflict, rule profiles, and timing depth were limited. |
| Rendering/exports | 8 | Many views and exports were listed, but deterministic rendering was absent. |
| Accessibility | 7 | Accessibility was included, but not with a conformance target or outline model. |
| Collaboration/versioning | 6 | Review and approval existed, but offline and merge behavior were incomplete. |
| Security/operations | 6 | Governance was acknowledged, but threat model and observability were thin. |
| Testing/pilot readiness | 7 | Test categories existed, but performance and human acceptance metrics were missing. |
| **Total** | **74/100** | Strong product blueprint; not yet state-of-the-art engineering specification. |

### Grade after this revision

| Category | Score | Assessment |
|---|---:|---|
| Football model | 10 | Covers units, elements, timing, conditions, variants, and role semantics. |
| Authoring UX | 10 | Defines creation, canvas, inspector, touch, keyboard, constraints, and teaching flows. |
| Asset library | 10 | Defines comprehensive asset families, manifests, metadata, lifecycle, and migration. |
| Architecture | 9 | Adds command/event architecture, deterministic state, APIs, and renderer boundaries. |
| Validation | 10 | Covers schema, structure, rule profiles, football completeness, conflicts, and explanations. |
| Rendering/exports | 10 | Adds deterministic SVG/vector rendering, parity, animation, hashes, and release bundles. |
| Accessibility | 9 | Sets WCAG 2.2 AA target and structured canvas navigation with text alternatives. |
| Collaboration/versioning | 9 | Adds offline recovery, domain conflicts, branches, merges, immutable releases, and rollback. |
| Security/operations | 9 | Adds tenancy, privacy, threat model, audit, observability, redaction, and AI controls. |
| Testing/pilot readiness | 10 | Adds performance budgets, visual/interaction tests, human research, and delivery gates. |
| **Total** | **96/100** | State-of-the-art build specification; remaining points require implementation evidence and pilot results. |

The revised score is intentionally not 100/100. The remaining points cannot be
earned by documentation alone: they require a functioning editor, real
organization testing, measured accessibility, security review, performance
evidence, and authorized production/pilot operation.

## 20. Current implementation mapping

The design described in this guide has now been implemented for the locally
testable NFL FIDOS scope. The authoritative implementation is distributed
across the Play Designer service, browser modules, rule-profile and asset
registries, and control/evidence artifacts rather than being a prototype-only
canvas.

- Asset authoring and the searchable palette: `playbook/asset-registry.json`,
  `src/nfl_fidos/play_design_service.py`, and `ui/play-designer-assets.js`.
- Interactive offense/defense authoring: `ui/play-designer-interactive.js`,
  `ui/play-designer-enhancements.js`, and the play-design contracts.
- Timeline, phase animation, QB reads, exchanges, rotations, pause markers,
  and narration: `src/nfl_fidos/play_timeline.py` and
  `ui/play-designer-timeline.js`.
- Organization sync, autosave, encrypted offline recovery, retries, server
  revision checks, conflict comparison, and branch preservation:
  `ui/play-designer-sync.js` and `src/nfl_fidos/play_design_service.py`.
- Collaboration: the append-only event log in
  `src/nfl_fidos/play_design_collaboration.py`, authenticated SSE streaming in
  `src/nfl_fidos/http_server.py`, short-poll fallback, presence/cursors,
  threaded comments, replies, resolution, and offline collaboration in
  `ui/play-designer-collaboration.js`.
- Versioning, publishing, diffs, branches, merges, rollback, renderer checksums,
  and game-plan snapshot locking: `src/nfl_fidos/play_design_versioning.py`
  and `ui/play-designer-versioning.js`.
- Teaching/player views, quizzes, mastery, and practice linkage:
  `ui/play-designer-teaching.js` and the teaching routes in `src/nfl_fidos/api.py`.
- Server-validated PDF, SVG, PNG, HTML, JSON, CSV, call-sheet, wristband, and
  install-sheet exports: `src/nfl_fidos/play_design_exports.py` and
  `ui/play-designer-export.js`.
- NFL, NCAA, high-school, youth, and flag legality profiles, explainable
  findings, source links, and owner-approved overrides:
  `src/nfl_fidos/play_legality.py`, `rules/play-design-rule-profiles.json`,
  and `ui/play-designer-legality.js`.
- Security, quality, accessibility, performance rehearsal, visual baselines,
  pilot metrics, and release gating: `src/nfl_fidos/security_controls.py`,
  `src/nfl_fidos/play_designer_quality.py`, `src/nfl_fidos/pilot_verification.py`,
  `control/security-threat-model.json`, and the `tests/` suite.

The local implementation evidence currently stands at 538 passing regression
tests and 97/97 evaluation families. The guide's production gates remain
intentional: real organization data, moderated coordinator/coach/player pilot
sessions, target-environment deployment and rollback, provider registration,
Stage 0 owner approval, and Stage 25 specification acceptance cannot be
fabricated or auto-approved by the software.

### Implementation addendum — position-first authoring and visual semantics (2026-08-26)

The current React Play Designer adds a coach-facing position toolkit to the
selected-player inspector. The toolkit derives a position family from the
player's position, role, and alignment key, filters out structural formation
and front assets, ranks active compatible registry assets, and recommends
reusable concept layers for the current unit. The supported role families are
quarterback, offensive line, backfield, eligible receiver, defensive front,
linebacker, secondary, and a safe general fallback. Each recommendation has a
description and timing guide; choosing it activates the existing canvas tool,
and choosing a suggested layer uses the canonical template materializer so the
action remains undoable, saveable, and versionable.

Assignment visuals are also persisted as first-class authoring data. Coaches
can set arrow/line meaning, remove the arrow, choose solid/dashed/dotted line
treatment, adjust stroke weight, and select round/square/butt line caps. The
SVG renderer honors those values in normal editing and synchronized playback,
while the existing assignment kind continues to drive football color and
validation semantics. This separation keeps visual notation flexible without
weakening the canonical assignment model.

The position toolkit also offers a one-click starting-action control. It
materializes an editable, bounded position-relative path with player and asset
ownership, route/run/block/coverage semantics, landmark and depth cues,
teaching text, line metadata, and synchronized timing. Motions begin on the
negative pre-snap timeline; every generated element enters the same reducer as
manually drawn work, preserving selection, undo, save, validation, versioning,
collaboration, and export behavior. Manual draw mode remains available beside
the one-click action.

Assignment geometry now supports canonical endpoint snapping to hashes, the
line of scrimmage, five-, ten-, and fifteen-yard landmarks, and the goal line.
The Depth (yards) control updates the actual final path point with
offense/defense-aware direction, retaining the route start and intermediate
handles. These edits are persisted on the canonical assignment and are
available to the same renderer, timeline, validator, and export pipeline.

Verification for this addendum: the React frontend passes 137 tests across 33
files, TypeScript typecheck passes, and the production Vite build passes. The
broader guide remains open for target-environment deployment, real organization
data, moderated pilot evidence, provider setup, full parity audit, and Stage 0
owner authorization.

### Implementation addendum — defensive responsibility presets (2026-08-27)

Defensive assignments now expose a structured responsibility-preset control in
the assignment inspector. The preset catalog covers fit rules (spill, box,
force, and cutback), coverage responsibilities (deep third, quarter match,
hook/curl, robber, man trail, and bracket), pressure (edge contain and A-gap
blitz), stunts (TEX and ET), and rotations (sky and spin). Applying a preset
writes coach-readable semantics into the canonical assignment: objective,
responsibility, gap or fit rule, zone, coverage, rush lane, stunt or rotation,
leverage, phase, and arrow meaning. The resulting geometry remains editable;
the preset is a starting point for authoring and never bypasses the server
legality validator.

This slice is implemented in `frontend/src/play-designer/defensivePresets.ts`
and `AssignmentGraphFields.tsx`, with explicit types for fit rules, coverage,
rush lanes, blitz paths, stunts, and rotations. Verification: 137 frontend
tests across 31 files pass, TypeScript typecheck passes, and the production
Vite build passes. Remaining defensive depth includes front/strength/gap
visualization, coverage-shell diagrams, rotation sequencing, and full
rule-profile validation against approved team terminology.

### Implementation addendum — semantic geometry and collision feedback (2026-08-27)

The canvas now distinguishes start, stem, break, and finish handles through
accessible descriptions and `data-handle-role` metadata. Assignment inspection
adds unit-aware angle presets for vertical, inside, outside, flat, and diagonal
breaks; selecting one changes the final geometry point and records the preset.
Timed intersecting route pairs are detected in the client and rendered with an
accessible possible-collision badge, giving the coach an immediate review cue
while preserving intentional crossings as a server-reviewed warning/error
decision. Verification: 137 frontend tests across 33 files pass, TypeScript
typecheck passes, and the production Vite build passes.

### Implementation addendum — partner-aware defensive exchanges (2026-08-27)

Defensive rush, stunt, and rotation assignments can now be linked as a
coordinated pair. Selecting an exchange partner writes the relationship to
both assignments, and the exchange-role selector records reciprocal semantics
for penetrate/loop, rush/replace, drop/replace, carry/transfer, and
rotate/replace relationships. The partner link is stored in `exchange_with`
and `target_element_id`; the role is stored in `exchange_role`, and the pair is
marked as an exchange phase for timeline and teaching views. Verification:
137 frontend tests across 33 files pass, TypeScript typecheck passes, and the
production Vite build passes.

### Implementation reconciliation addendum — current asset catalog and export safety (2026-08-29)

The live canonical asset registry has since expanded to 128 governed assets
across formation, route, motion, run, protection, block, front, coverage,
pressure, stunt, rotation, check, and teaching families. The registry remains
versioned, searchable, lifecycle-aware, alias-aware, thumbnail-backed, and
compatibility-aware, and it is consumed directly by the React asset palette.
The Play Designer export pipeline now also rejects malformed or out-of-bounds
player, primary-path, and alternate-branch coordinates before rendering, with
exact source paths in the validation findings. These updates close the local
catalog and clipping-safety gaps; organization-specific catalog administration,
printer/device certification, and production deployment remain separate
acceptance requirements.

Draft/export geometry consistency addendum — 2026-08-29: the canonical play
validator now applies the field-bounds and minimum-path contract to alternate
route branches as well as primary paths. Malformed branch objects, short branch
paths, malformed points, and out-of-bounds coordinates are reported with
deterministic `DESIGN-*` paths before a draft can be treated as valid. Export
preflight applies the corresponding `EXPORT-*` checks, so draft validation and
artifact validation cannot disagree about clipped alternate geometry.

### Implementation addendum — route corridor intent and explanations (2026-08-28)

Route collisions now produce an explainable pair report. The inspector identifies
the other route in the active timing window, offers `Needs review`, `Intentional
crossing`, and `Avoid crossing` states, and stores a coach-authored explanation.
An intersection is considered intentional only when both participating routes
explicitly opt in; this keeps an accidental crossing visible while supporting
meshes, picks, and other designed crossing concepts. Verification: 151 frontend
tests across 40 files pass, TypeScript typecheck passes, and the production Vite
build passes. This remains a client authoring aid; final legality and collision
approval remain server-controlled.

### Implementation addendum — branch-aware teaching and QB-read cues (2026-08-28)

Alternate route paths now participate in synchronized teaching authoring. When
an assignment has a primary route plus alternate branches, the timeline exposes
a path selector, and ball, handoff, QB-read, exchange, rotation, and narration
cues persist the selected `branch_id`. Cue labels identify the selected path so
the teaching/player view and downstream consumers can distinguish the primary
read from a conditional answer. Verification: 155 frontend tests across 41
files pass, TypeScript typecheck passes, and the production Vite build passes.

### Implementation addendum — interactive coverage-shell authoring (2026-08-28)

The defensive coverage-shell editor now includes a spatial SVG authoring map in
the inspector. Coaches can click or keyboard-focus deep, underneath, robber,
bracket, and man regions to toggle declared shell responsibilities, see the
active-region state and declared count, and retain the accessible checkbox
controls. Changes continue to write the canonical `coverage_zones` metadata and
remain visible on the field canvas. Verification: 155 frontend tests across 41
files pass, TypeScript typecheck passes, and the production Vite build passes.

### Implementation addendum — post-snap rotation lane (2026-08-28)

Rotation assignments are now summarized as a connected, ordered lane in the
defensive inspector. The lane sorts authored sequence numbers, shows the
trigger-to-replacement label, surfaces reciprocal exchange partners, and lets a
coach jump directly into any rotation assignment. It is a view over the
canonical assignment graph, so edits continue to flow through validation,
timeline, teaching, review, versioning, and export. Verification: 157 frontend
tests across 41 files pass, TypeScript typecheck passes, and the production Vite
build passes.

### Implementation addendum — direct defensive exchange authoring (2026-08-28)

Selecting exactly two defensive assignments now exposes a relationship authoring
card. Coaches choose a semantic exchange role and create both reciprocal links
with one action; the pair then appears as a single selectable relationship on
the field. The canonical pair patch preserves role reciprocity, exchange phase,
target relationship, timeline meaning, and downstream validation/export data.
Verification: 163 frontend tests across 42 files pass, TypeScript typecheck
passes, and the production Vite build passes.

### Implementation addendum — defensive responsibility validation (2026-08-28)

The Checks panel now supplements authoritative server legality with explainable
draft graph findings. It detects missing exchange partners, non-reciprocal
links, role/assignment mismatches, missing replacement zones for replacement
roles, duplicate rotation sequence numbers, and declared shell zones without
an owner. Findings include a stable code, path, severity, and suggested action;
they remain reviewable/overrideable and never bypass server approval. Verification:
163 frontend tests across 42 files pass, TypeScript typecheck passes, and the
production Vite build passes.

### Implementation addendum — defensive teaching context (2026-08-28)

Role-view step generation now carries gap ownership, exchange partner and role,
replacement zone, rotation trigger, and sequence context. The player dialog
renders those values as responsibility chips beside the authored instruction,
while the accessible read-through includes the same contextual language. A
player sees the action they own and the exchange they participate in; the coach
view retains the full defensive context. Verification: the focused Python
teaching-context test passes, the frontend teaching suite passes, TypeScript
typecheck passes, and the production Vite build passes.

### Implementation addendum — phase-level exchange mastery (2026-08-28)

Role-view steps now carry a `mastered` state derived from the organization’s
mastery records. Before-exchange, exchange, and replacement phases can therefore
be recorded and displayed independently in the player view, while practice
references and quiz/mastery APIs remain linked to the canonical step id.
Verification: the focused Python mastery and defensive-teaching tests pass, the
full frontend suite passes, TypeScript typecheck passes, and the production Vite
build passes.

### Implementation addendum — practice responsibility outcome linkage (2026-08-28)

Practice outcome recording now persists optional canonical play-assignment,
teaching-step, and responsibility-phase references alongside the period, play,
drill, film, and evidence lineage. Coaches can score read, exchange-trigger,
replacement/fit, and finish phases independently; the fields remain available
to Analytics for sample-aware outcome reporting. Verification: 594 Python tests
pass with the standard-library runner, 163 frontend tests across 42 files pass,
TypeScript typecheck passes, and the production Vite build passes.

### Implementation addendum — export branch and drawing fidelity (2026-08-28)

SVG and HTML exports now preserve alternate route/assignment branches, branch
conditions, and authored line semantics including style, weight, and cap. The
accessible assignment text also describes conditional paths and their timing so
the exported artifact remains useful beyond the visual diagram. The controlled
local visual baseline was regenerated from the deterministic renderer after this
intentional change. Verification: 596 Python tests pass, 163 frontend tests
across 42 files pass, typecheck/build pass, and Play Designer quality gates pass.

### Implementation addendum — raster and PDF branch parity (2026-08-28)

PDF and PNG renderers now carry alternate branch geometry into generated field
artifacts, preserving the same base/alternate path model used by SVG and HTML.
Branch paths receive distinct visual treatment in the PDF renderer and remain
visible in raster output when the optional imaging dependency is available; the
minimal packaging fallback remains valid and fail-safe. Verification: 597 Python
tests pass, 163 frontend tests across 42 files pass, typecheck/build pass, and
the Play Designer quality gates pass.

### Engineering references used for this revision

- [W3C Web Content Accessibility Guidelines 2.2](https://www.w3.org/TR/WCAG22/)
  — accessibility target and authoring-tool requirements.
- [MDN SVG pointer-events reference](https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Attribute/pointer-events)
  — interactive vector hit-testing behavior.
- [Yjs collaborative editor documentation](https://docs.yjs.dev/getting-started/a-collaborative-editor)
  and [offline editing documentation](https://docs.yjs.dev/getting-started/allowing-offline-editing)
  — reference patterns for awareness, shared updates, and offline recovery.

### Implementation addendum — timeline integrity preflight (2026-08-28)

The React Checks panel now performs a local timeline-integrity pass before a
draft is sent to the authoritative Python API. It identifies stale assignment
and player references, duplicate event IDs, invalid or out-of-clock event
windows, route-branch references that no longer exist, invalid assignment
windows, phases outside their parent assignment, and overlapping phases. These
findings are authoring safeguards only; server legality and governed release
decisions remain authoritative. Verification: the full frontend suite passes
with 228 tests, TypeScript typecheck passes, and the production Vite build
passes.

### Implementation addendum — blocking relationship safeguards (2026-08-28)

Offensive blocking authoring now validates reciprocal combo relationships,
ensures combo partners are blocking/run surfaces, requires explicit protection
threats for man/slide/scan modes, and rejects stale protection-target links.
These checks supplement existing pull, trap, wrap, fold, insert, arc, combo,
screen, target, and self-reference diagnostics. Verification: focused blocking
tests pass, the full frontend suite passes with 229 tests, TypeScript typecheck
passes, and the production Vite build passes.

### Implementation addendum — timed route collision corridors (2026-08-28)

Route-collision records now retain the exact primary or alternate-path geometry
that participates in the timed overlap. The field renders a distinct corridor
overlay, brightens it during the active playback interval, distinguishes
intentional crossings from unresolved intersections, and exposes the same
explanation to assistive technology. The corridor is clipped to the exact
overlap subpath rather than implying that the entire route is in conflict.
Verification: the full frontend suite passes with 230 tests, TypeScript
typecheck passes, and the production Vite build passes.

### Implementation addendum — first-class alternate route editing (2026-08-28)

Alternate route branches are now independent editable paths on the canvas.
Branch handles support pointer drag, keyboard nudging, and direct double-click
handle insertion without moving the parent route. Branch-specific route family,
stem depth, break type/depth, and finish direction metadata remain synchronized
with the edited geometry, timing window, branch condition, collision model,
teaching view, and export pipeline. Verification: the full frontend suite passes
with 231 tests and 46 test files, TypeScript typecheck passes, and the
production Vite build passes.

### Implementation addendum — professional asset catalog expansion (2026-08-28)

The canonical asset registry now contains 113 versioned, searchable assets
across formation, route, motion, run, protection, block, front, coverage,
pressure, stunt, rotation, check, and teaching families. The expanded catalog
adds professional front variants (under, even, odd, mint, wide, reduced,
nickel, dime, goal-line, and custom), split-field and match coverage variants,
interior/overload/creeper/green-dog/spy/contain pressures, line-game movement
(TE, twist, pirate, long-stick, pinch, slant, and loop), spin/buzz/poach
rotations, and reach/down/trap/wrap/fold/climb/scoop/insert/arc/screen-release
blocking with full-slide and scan protection. Existing aliases, descriptions,
accessibility text, lifecycle fields, thumbnails, and compatibility metadata
remain governed by the registry contract and flow directly to the React asset
palette. Verification: the Python registry contract passes, 22 focused
service tests pass, the full frontend suite passes with 231 tests, typecheck
passes, and the production Vite build passes.

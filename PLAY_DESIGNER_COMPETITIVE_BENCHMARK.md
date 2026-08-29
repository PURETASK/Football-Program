# Play Designer Competitive Benchmark and Product Target

Status: active top-priority implementation stream under the NFL Football Intelligence OS Master Codex goal  
Benchmark date: 2026-08-25  
Product rule: reproduce useful capabilities and workflow outcomes through original code, interaction design, terminology controls, and visual assets. Do not copy proprietary source code, protected artwork, brand identity, or trade dress.

## Product target

The NFL FIDOS Play Designer must combine the fastest professional diagram-authoring workflow with a deeper football model, controlled collaboration, explainable legality checks, synchronized teaching, and release-grade outputs. The editor is not considered state of the art merely because it can draw arrows. A play must remain one canonical, structured object from initial concept through staff review, player study, practice, game-plan release, export, and outcome analysis.

## Official products reviewed

| Product | Strongest qualities observed | Original NFL FIDOS equivalent |
|---|---|---|
| [PQD Playbook / Play Editor](https://help.proquickdraw.com/helpcenter/play-editor-overview) | Reusable drawing and shape libraries, custom route trees, instant horizontal/vertical flipping, layer ordering, auto naming, template-driven install and scout-card production | Organization-owned asset registry; reusable formation/concept/route fragments; hash- and strength-aware mirroring; semantic layers; terminology-based naming recipes; multi-format release templates |
| [FirstDown PlayBook](https://firstdown.playbooktech.com/) | Large editable play catalog, offense/defense/special-teams content, plays shown against multiple looks, reusable stencils, field-format choices, lineman view, wristband and practice outputs | Approved professional starter catalog; play families with opponent-look variants; reusable partial-play components; league-aware fields; position-focus views; verified PDF/SVG/PNG/call-sheet/wristband/install outputs |
| [GoArmy Edge Football](https://www.goarmyedge.com/football) | Precise alignment and first-step movement, route trees, shifts/huddles, accurate timing and ball handling, 2D/3D and player perspective, drills and quizzes | Stable alignment keys; field/hash/LOS controls; assignment phases and exchanges; synchronized ball/read/rotation events; coach, position-group, and player perspectives; teaching steps, quizzes, and mastery records |
| [Hudl Play Tools](https://www.hudl.com/products/playtools) | Never-redraw templates, targeted install sharing, study activity, film-linked practice scripts, multi-device and offline access | Deduplicated concept templates; audience-scoped releases; study/mastery telemetry; evidence links to film and practice; encrypted offline approved-content cache and conflict-safe synchronization |
| [Playmaker X](https://play.google.com/store/apps/details?id=com.wearetrue.playmakerx.tackle) | Touch-first authoring, one-tap animation with speed tuning, roster-to-position assignment, instant flip, player-count formats, visual line/end-cap vocabulary, broad printing | Tablet-first pointer controls; timeline speed and cue controls; roster/personnel bindings; semantic mirror; rule-profile/player-count formats; canonical route/block/motion symbols; production export composer |

## State-of-the-art capability standard

1. **Professional canvas precision** — drag-to-draw, handles, snapping, marquee, pan/zoom, keyboard nudging, linked player-path movement, multi-select, grouping, locking, layers, copy/paste, and semantic mirroring.
2. **Intelligent asset system** — searchable, filterable, thumbnail-driven, lifecycle-controlled assets with aliases, compatibility scores, replacements, migrations, and organization terminology.
3. **Formation and alignment authoring** — stable 11-player presets, field/hash/LOS/strength/direction controls, reusable huddles and shifts, eligibility/alignment metadata, and offense/defense/special-teams contexts.
4. **Structured assignment graph** — every route, block, rush, fit, coverage, motion, read, and exchange can record its owner, target, dependency, technique, landmark, leverage, gap/zone, objective, and timing relationship.
5. **Multi-track timeline and animation** — per-element timing, football phases, speed control, marker stepping, pause cues, narration, reads, exchanges, coverage rotations, ball movement, and player/coach perspectives.
6. **Live explainable football checks** — the unsaved draft is checked after edits for structure, reference integrity, dependency cycles, assignment conflicts, route/protection/coverage/fit issues, and selected rule profile; every finding identifies its path and remedy context.
7. **Play families and reusable concepts** — save whole plays or selected components, apply them against multiple fronts/coverages, retain inheritance, show local overrides, auto-name through organization recipes, and avoid redrawing.
8. **Staff-grade collaboration and version control** — presence, cursors, threaded element comments, assignments, resolution states, immutable snapshots, visual and element-level diffs, guarded merges, rollback, checksums, and release locks.
9. **Teaching and player comprehension** — filtered diagrams, player-only animation, position-group views, step-by-step reads, accessible text, quizzes, mastery, coaching notes, practice links, and approved offline delivery.
10. **Production output fidelity** — branded and black-and-white PDFs, scalable SVG, PNG, play grids, install sheets, scout cards, multi-play call sheets, true wristband dimensions, page numbering, signatures/checksums, and server-side validation.

## Competitive differentiators NFL FIDOS must preserve

- One structured play object powers the canvas, animation, validation, teaching view, collaboration history, and every export. No slide or image becomes the hidden source of truth.
- Football terms remain normalized while each organization can supply aliases and naming conventions.
- Confidence, evidence, rule profile, ownership, decision references, and approved overrides remain visible instead of being flattened into a generic drawing.
- Defensive authoring has equal depth to offensive authoring, including front, coverage, pressure, fit, stunt, exchange, leverage, and rotation logic.
- Every release is attributable and reproducible through a design checksum, renderer checksum, immutable snapshot, and approval record.

## Current implementation mapping

| Capability | Current state | Next acceptance threshold |
|---|---|---|
| Canvas precision | Implemented and tested | Preserve while adding richer semantic handles and tablet verification |
| Intelligent assets | Formation/front compatibility and lifecycle integration implemented | Complete route/concept fragment reuse, naming recipes, and organization catalogs |
| Formation/alignment | 13 professional 11-player presets, field translation, and authored pre-snap sequence implemented | Add formation spacing dimensions, role constraints, and deployment-environment verification |
| Assignment graph | Structured references, cycle/conflict validation, graph summary, and inspector controls implemented | Expand production-scale administration and multi-client convergence evidence |
| Timeline | Basic synchronized playback exists | Multi-track phases, speed, cue stepping, pauses, narration, exchanges, and ball events |
| Live checks | Saved-design legality exists | Debounced, non-persisting validation of the current unsaved draft |
| Templates/play families | Registry-backed templates, partial stencils, inheritance, naming, and batch variants exist | Multi-client convergence, richer catalog governance, and production-scale template administration |
| Collaboration/versioning | Presence, shared cursors, comments, events, snapshots, branching, diffs, merge conflicts, release locking, and rollback exist | Production multi-client convergence and deployment-environment collaboration evidence |
| Teaching | Role-filtered diagrams, mastery, player animation, progressive reveal, accessible text, quizzes, and practice links exist | Moderated player pilot evidence and production learning-data integration |
| Exports | Server PDF/SVG/PNG/HTML/JSON/CSV, install sheets, call sheets, wristband layouts, branding, and render preflight exist | Provider-grade fidelity, printer/device certification, and production deployment evidence |

## Definition of done for this workstream

This priority is complete only when all ten capability areas are implemented, connected to organization-scoped persistence, covered by backend and frontend tests, verified in the production bundle, exercised through tablet and keyboard workflows, checked for screen-reader and contrast behavior, traced into the Master Codex audit, and supported by a coach-facing tutorial. Competitive research alone, static mockups, or isolated controls do not satisfy completion.

## Implementation addendum — 2026-08-25

The benchmark is now an active engineering standard, not a research-only note. The latest React slice adds an organization-backed concept-template registry with 17 approved offense/defense starter packages, compatibility-aware palette integration, relative geometry materialization, layer application, and save-current-play template capture. The catalog now spans Dagger, Flood, Mesh, Inside Zone RPO, Half Slide, Cover 3 Buzz, Quarters Match, Sim Pressure, Empty Quick Choice, Counter GT, TEX / ET, Smash, Stick, Four Verticals, Power O, Cover 1 Robber, and Cover 2 Trap. Pre-snap motion is preserved from -5,000 ms and timeline event aliases are normalized into canonical ball, shift, motion, exchange, read, rotation, and pause events.

Version review now returns the immutable base and compare designs alongside element-level diff data. The Review panel can toggle a non-interactive field overlay with dashed compared paths, ghost personnel, and an accessible legend; this keeps review evidence visible on the same field as the active draft. The teaching surface now renders the filtered role/position-group diagram, dims context players, progressively reveals authored steps, and replays the active assignment with accessible play/pause/replay controls.

Verification for this historical addendum: the full frontend suite passed 116 tests across 27 files; the focused Play Designer service/API/export suite passed 23 tests; TypeScript typecheck passed; and the production build passed with the Play Designer route chunk at 89.48 kB. The partial-stencil, inheritance, batch-variant, export, and teaching gaps named at that point have since been reconciled by later implementation addenda; current remaining gaps are listed in the dated capability reconciliation below.

The export slice now adds a source manifest and manifest hash to every generated artifact. Each manifest records the selected design IDs, versions, immutable snapshot IDs, content checksums, renderer versions/checksums, status, release IDs, and approval state; signed exports include the manifest hash in their HMAC-covered fields. The export dialog shows this source lock before download so a packet can be traced back to the exact canonical play revision used to render it.

The export dialog also exposes audience selection for coach/staff, player, and position-group views. Role-filtered artifacts reuse the canonical visibility rules used by teaching views, so a player packet can be focused without creating a second unsynchronized play record.

Wristband delivery now supports validated standard two-column, compact three-column, and four-column sideline-strip layouts. Each layout has explicit capacity, card width, typography, and truncation rules, and non-wristband artifacts cannot request wristband layouts.

Export preflight addendum (2026-08-26): the export workflow now has a non-rendering `POST /v1/playbook/designs/export/preflight` check. It resolves the same effective layout used by the renderer, validates every organization-scoped source design and audience role, returns explainable warning/error issues, and computes the source manifest hash before content generation. The React dialog requires a fresh matching preflight after any packet, format, layout, or audience change and keeps artifact generation locked while blockers remain. Preflight responses intentionally contain no rendered content, and the final artifact still revalidates before signing.

Install handout addendum (2026-08-26): PDF install-sheet output now uses a dedicated coaching layout with a branded header, canonical field diagram, assignment ledger, player/position ownership, landmark and timing cues, and teaching notes. It preserves role filtering and black-and-white rendering, while CSV remains available for downstream roster or install-card workflows.

Position authoring addendum (2026-08-26): selecting one player icon in the designer inspector now opens a position-aware toolkit backed by the canonical asset registry and concept-template library. Quarterback, offensive-line, backfield, eligible-receiver, defensive-front, linebacker, and secondary profiles rank compatible route, motion, run, blocking/protection, coverage, rush, stunt, fit, read, check, and teaching actions; each option displays an accessible description and timing guide, activates the existing draw tool, and preserves the normal undo/save path. The toolkit also suggests unit- and role-relevant reusable template layers that can be inserted directly into the current call. Frontend verification now passes 125 tests across 30 files, TypeScript typecheck passes, and the production build passes.

Visual authoring addendum (2026-08-26): assignment inspection now includes explicit arrow/line meaning, no-arrow mode, end/start/both/none arrowheads, smooth versus sharp path geometry, solid/dashed/dotted treatment, line-weight, and line-cap controls. The selected path renders those choices on the canonical SVG canvas and continues to animate against the same timeline path. This keeps route, block, motion, run, coverage, rush, stunt, and annotation semantics legible in both live editing and playback; the production build and 125-test frontend suite remain green.

Action materialization addendum (2026-08-26): position recommendations now offer a separate one-click “Add starting action” control in addition to manual draw mode. The new materializer generates bounded, position-relative geometry for routes, motions, runs, blocks/protections, coverage, rushes, stunts, fits, and fallback actions; links the new element to its player and registry asset; applies timing, pre-snap/post-snap phase, landmark, depth, assignment, teaching, arrow, and line metadata; and returns the element through the normal editor reducer for selection, undo, save, version, validation, collaboration, and export. Motion actions are automatically placed on the negative pre-snap timeline. Pure materialization behavior is covered by dedicated tests.

Pre-snap sequence addendum (2026-08-28): the inspector now authors an
organization-persisted sequence of huddle, shift, motion, set, and cadence
steps, each with an explicit order, label, start/end time, and coaching note.
The sequence is modeled separately from post-snap assignment timing so a coach
can teach the cadence and movement phase without corrupting route, block, read,
or coverage clocks. The controls are keyboard-accessible, removal is explicit,
and the new sequence metadata travels with the canonical play object for save,
version, validation, teaching, collaboration, and export consumers.

Geometry authoring addendum (2026-08-26): assignment controls now include landmark snapping to hashes, the line of scrimmage, five-, ten-, and fifteen-yard landmarks, and the goal line. Editing Depth (yards) now updates the actual path endpoint using unit-aware offensive/defensive direction while retaining the authored start and intermediate handles. These are geometry mutations, not display-only labels, and remain compatible with the existing handle editor, sharp/smooth rendering, timeline, and validation flows.

Defensive authoring addendum (2026-08-27): defensive assignments now provide a
grouped responsibility-preset control in the inspector. The catalog includes
spill/box/force/cutback fits, deep-third/quarter-match/hook-curl/robber/
man-trail/bracket coverage, edge and A-gap pressure, TEX/ET stunts, and
sky/spin rotations. A selection applies explicit coach-readable fields for
gap, fit rule, zone, coverage, rush lane, stunt/rotation, objective,
responsibility, leverage, phase, and diagram arrow meaning. Presets are
authoring starters and remain subject to the server legality validator. The
frontend suite now passes 137 tests across 33 files, with passing typecheck and
production build. Remaining parity work is coverage-shell visualization,
front/strength authoring, rotation sequencing, and full rule-profile depth.

Geometry semantics addendum (2026-08-27): the editor now provides unit-aware
angle presets, accessible start/stem/break/finish handle roles, and visible
possible-collision feedback for timed intersecting routes. Angle selection
mutates the canonical endpoint; collision feedback is intentionally advisory
and remains consistent with server legality and coach override workflows.
Verification is 137 frontend tests across 33 files with passing typecheck and
production build.

Partner-aware exchange addendum (2026-08-27): defensive rush, stunt, and
rotation assignments can now be linked as reciprocal graph relationships.
Partner selection updates both assignments; explicit roles cover
penetrate/loop, rush/replace, drop/replace, carry/transfer, and rotate/replace
semantics. The link is persisted for timeline, teaching, validation, review,
and export consumers. Verification is 137 frontend tests across 33 files with
passing typecheck and production build.

## Capability reconciliation addendum — 2026-08-28

The benchmark’s earlier “remaining parity” note has been reconciled against
the current implementation. The following capabilities are now implemented in
the React designer and are covered by the existing editor, geometry,
defensive-authoring, timeline, API, and export tests:

- Interactive spatial coverage-shell visualization with keyboard-accessible
  zone toggles and canvas rendering.
- Defensive front and strength authoring, including technique, alignment
  relationship, canonical alignment keys, and formation-strength controls.
- Full gap-ownership visualization with selectable owners, conflict states,
  anchor links, and explainable unassigned gaps.
- Rotation sequencing with trigger, order, vacated responsibility,
  replacement zone, replacement defender, and communication fields.
- Debounced, non-persisting validation of the current unsaved draft.
- Multi-track timeline controls for phases, markers, narration, ball events,
  reads, exchanges, rotations, playback speed, and pause cues.

The remaining benchmark gaps are narrower and still active: true multi-user
edit convergence under concurrent mutations, complete provider-grade export
layout/device certification, authoritative depth for every supported rule
profile, automated browser visual/screen-reader/tablet traces, and moderated
coach/coordinator/player pilot evidence. Governed parent change propagation is
implemented locally: the impact report is read-only by design, while an
owner-approved proposal performs fingerprint-checked versioning and descendant
propagation. Partial-play stencil capture, inheritance, and persisted
multi-look assignment transformations are also implemented locally, but they
still require production-scale administration and real-team pilot evidence
before they can be considered operationally complete.

## Template integrity addendum — 2026-08-29

The canonical template loader now performs pre-editor integrity checks for
assignment timing bounds, timeline duration, marker metadata, duplicate marker
identities, and all partner/dependency/target references. Defensive exchange
partners therefore cannot silently point at a missing assignment, and timeline
markers cannot collide or fall outside the supported pre-snap/play window.
Invalid catalog records fail closed during load and are covered by regression
tests alongside the 17 approved system templates.

## Export print-profile addendum — 2026-08-29

Rendered exports now carry an explicit print profile, orientation, safe-area
margin, and color-mode declaration. Visual artifacts use a letter portrait
profile (with a tighter wristband safe area), while CSV and JSON artifacts use
a non-printing data-export profile. Artifact verification rejects mismatches,
so delivery metadata cannot describe a data payload as printer-safe or omit
the intended black-and-white mode.

The local quality suite now includes a deterministic two-editor convergence
rehearsal. It proves that disjoint formation/assignment edits converge to the
same checksum regardless of merge order and that overlapping edits preserve a
stable, explicit conflict path. This is stronger local merge evidence, but it
does not replace network, transport-ordering, browser, or production-scale
multi-client validation.

Collaboration retry addendum — 2026-08-28: Play Designer collaboration events
now accept an optional actor-scoped idempotency key. A retried identical event
returns the original sequence and event identity; reusing a key with a
different event type or payload is rejected. This gives offline outbox and
retry adapters a deterministic server boundary while preserving monotonic
replay ordering. Client SSE consumers continue to reject duplicates and hold
gaps for replay. Network partition, multi-browser, and production transport
ordering tests remain external acceptance work.

Authenticated stale-save addendum — 2026-08-29: the API regression contract
now proves that two editor snapshots loaded at one revision cannot overwrite
one another. The first save advances the canonical revision; the stale second
save returns HTTP 409 with the conflict code, expected revision, actual server
revision, and server snapshot required by the client three-way merge path.
This strengthens local multi-editor evidence without claiming networked
multi-browser or production-scale convergence.

Export-matrix addendum — 2026-08-29: the local quality gate now renders a
14-case matrix across play-card, call-sheet, wristband, and install-sheet
families, including visual, data, HTML, and print layouts. Each artifact must
self-verify its integrity, retain the requested layout, and carry non-empty
payload metadata before the matrix passes. This strengthens renderer coverage
without substituting for target printer/device certification or deployment
environment validation.

Repository verification for this reconciliation: the frontend suite passes
279 tests across 49 files, the Python suite passes 693 tests, TypeScript
typecheck and the production build pass, and the local Stage 0 runtime smoke
validates the React routes, static assets, authenticated Playbook/catalog
surfaces, and non-activating governance evidence path. Those results prove the
local foundation; they do not prove production deployment, real organization
adoption, moderated pilot outcomes, or owner approval.

## Partial stencil capture addendum — 2026-08-28

The reusable-template workflow now supports a deliberate selection scope. A
coach can multi-select assignment elements in the canonical editor, open the
template library, choose **Capture only the selected assignments**, and save a
relative organization-scoped stencil. The API accepts `element_ids`, filters
the immutable source snapshot to that selection, retains only relationships
inside the captured subset, records `capture_scope=selection`, and preserves
the selected source IDs for provenance. Full-play capture remains the default.
The stencil still re-enters the normal template materializer, so it receives
slot-relative geometry, player binding, namespaced timing, undo, validation,
save, version, collaboration, teaching, and export behavior. This closes the
basic partial-capture path; inherited parent stencils, multi-look batch
variant generation, and visual inheritance/override diffing remain open.

The first lineage slice is now implemented as well. When capturing a new
organization template, staff may optionally select an existing compatible
package as its parent. The saved child records `parent_template_id` and a
resolved `inherited_assignments` payload; child assignments take precedence
by assignment key during materialization. The library displays the inherited
parent so a coach can distinguish a reusable variation from an unrelated
copy. This establishes traceable parent reuse while leaving parent-change
propagation and multi-look batch generation for the next slice. Verification
for this slice is 166 frontend tests and 24
focused Play Designer backend/API tests, with typecheck and production build
passing locally.

The lineage boundary is now visible before and after application. Template
previews render inherited paths with a lighter dashed treatment and local
paths with the normal emphasis; package metadata reports total, inherited,
and local assignment counts. Materialized elements carry an explicit
`template_assignment_origin` value, allowing later comparison and teaching
surfaces to distinguish inherited responsibilities from child overrides
without reconstructing provenance from labels.

## Multi-look variant engine addendum — 2026-08-28

The canonical Python service and organization-scoped API now generate bounded
batches of up to 32 draft child designs from an explicit source play. Each
variant applies a controlled look patch (formation, front, coverage,
personnel, concept, or rule profile), receives its own identity, revision,
checksum, immutable save snapshot, and validation result, and records
`parent_design_id`, `variant_batch_id`, and a `variant_look` payload containing
the label, patch, source design, and source revision. The persisted batch report
retains every generated child and marks the result human-review-required.
This makes multi-look generation operationally traceable and reviewable while
leaving variant-specific assignment transformations, visual batch comparison,
approval/release bundling, and provider-grade export certification for the
next slice.

The first visual comparison slice is now present in the Concepts panel. Each
generated child displays a structured source diagram beside its variant
diagram, the look patch, validation/revision state, and a direct route into the
child editor. The comparison is rendered from canonical players and element
geometry, so it remains inspectable and does not introduce an image as a
second source of truth. Full element-level diffing and variant-specific
transformation remain open.

Element-level variant diffing is now implemented in the review rail. Each
source/child comparison reports changed metadata fields plus added, removed,
changed, and unchanged assignment counts; changed assignment records retain
their exact field names. This is a deterministic comparison of structured
play records and is separate from the visual diagrams, giving staff an
explainable review signal before they open or approve a child. Full side-by-
side field-level expansion and variant-specific transformations remain open.

The review rail now expands those deterministic diffs inline. **Inspect
field-level changes** reveals changed metadata names, changed assignment IDs
with exact field names, and added/removed assignment IDs without requiring a
coach to open each child editor. The expansion is native disclosure markup,
keyboard reachable, and backed by a component regression test. Variant-specific
assignment transformations and provider-grade release certification remain
open. Changed assignment fields now also show their structured before/after
values, preserving the exact semantic delta for review rather than requiring
staff to infer it from the diagrams.

Merge conflicts now have the same level of review detail. Each server-reported
conflict path is an accessible expandable item showing the base, target, and
branch values plus the server explanation when supplied. This makes an
overlapping edit actionable for staff while keeping the merge paused for an
authorized human decision.

Generated look variants now accept an optional bounded assignment-transformation
recipe. Each recipe targets a stable element ID and applies a validated set of
route, timing, blocking, protection, coverage, pressure, rotation, drawing, or
teaching fields to every generated child. Unknown targets and unsupported fields
are rejected before persistence, and the normalized recipe is retained in
`variant_look.assignment_patches` for diffing, review, and provenance. This
allows a coordinator to express a controlled answer adjustment without
silently inventing football semantics; server legality and human approval still
govern the resulting child designs.

Governed lineage propagation addendum — 2026-08-28: organization-owned child
templates can now receive a bounded semantic change proposal against a stable
assignment key. A coach submits the proposal with an immutable source
fingerprint and the system records a read-only impact report; a separate
program-owner approval is required. Approval rechecks the fingerprint, bumps
the parent version, applies only the allowlisted fields, refreshes inherited
assignment snapshots through descendants, preserves child-local assignments,
marks affected active packages for review, and records every propagated ID in
the proposal audit record. System templates cannot be mutated through this
workflow.

## Template lineage review addendum — 2026-08-28

The Concepts panel now exposes a pre-application inheritance review for child
packages with a resolved parent. It compares stable assignment keys and
semantic fields, then reports inherited-unchanged assignments, local child
additions, and exact overridden fields such as route type, landmark, timing,
protection, or coverage. The disclosure is keyboard reachable and uses the
same resolved assignment model that drives preview and materialization, so the
review cannot drift into a second visual-only representation. This closes the
local visual inheritance/override explanation gap; parent-change propagation,
network-scale administration, and production pilot evidence remain external
acceptance work.

Two-client HTTP rehearsal addendum — 2026-08-28: the HTTP test suite now
opens the authenticated Play Designer stream as two distinct organization
sessions, confirms both receive the same canonical sequence, creates a later
event, and reconnects from `since=1` to receive only sequence 2. This proves
the local HTTP/SSE replay contract in addition to the event idempotency and
client cursor unit tests. It remains a bounded local rehearsal; real browser
latency, network partitions, transport reordering, and production-scale
multi-client persistence still require deployment validation.

Variant history addendum — 2026-08-28: generated multi-look batches are now
discoverable after a refresh through the organization-scoped
`GET /v1/playbook/designs/variants` endpoint. Staff can optionally filter by
`source_design_id`; the response preserves batch identity, source lineage,
draft child designs, transformation recipes, immutable source revision, and
the human-review-required state. The Play Designer workspace payload includes
the same newest-first batch history, so later UI surfaces can restore review
sets without relying on a transient browser result. The endpoint is read-only
and does not approve, publish, or release any generated child.

Variant review readiness addendum — 2026-08-28: the persisted batch response
now includes a computed, non-mutating review summary for every child look. It
identifies missing children, invalid validation state, non-draft lifecycle
state, existing release identity, ready-for-review children, and aggregate
ready/blocked counts. The Concepts panel surfaces that count beside each saved
review set. This gives staff an explainable pre-approval gate without turning
batch generation into an automatic publish operation.

Governed variant review addendum — 2026-08-28: a ready persisted batch can now
be submitted as one review request through
`POST /v1/playbook/designs/variants/request-review`. The service validates all
children before mutating any of them, transitions every valid draft child to
`under_review` with a shared decision reference, records the batch request, and
emits collaboration events for each child. Any missing, invalid, or already
transitioned child blocks the whole request, preserving atomic review intent;
owner publishing remains a separate per-design authorization boundary.

Owner batch-approval addendum — 2026-08-28: program owners can now approve a
complete variant batch for release through
`POST /v1/playbook/designs/variants/approve-review`. The operation rechecks
every child, records the owner decision and batch approval metadata, emits
collaboration events, and deliberately leaves child lifecycle and release
creation under the existing per-design publish controls. No batch approval can
bypass legality, checksum, or human-release requirements.

Governed lineage UI addendum — 2026-08-29: the React Concepts panel now exposes
the organization-owned lineage workflow end to end. Staff can inspect descendant
impact, inherited counts, local overrides, and inheritance depth; select an
assignment field and value to create a bounded proposal; and see the proposal
status and decision identity. A program-owner session alone receives the
approval control, which calls the existing fingerprint-rechecked propagation
service and reports affected packages moved to review. System templates remain
immutable, and child-local overrides remain preserved. Remaining acceptance work
is provider-scale administration, network/multi-browser convergence, and real
organization pilot evidence.

Export geometry safety addendum — 2026-08-29: export preflight now rejects
player alignments, primary paths, and branch paths that contain malformed or
out-of-bounds coordinates. Findings identify the exact player, element, branch,
and point path, preventing clipped or misleading PDF, SVG, PNG, and HTML
artifacts from being rendered. This complements source-lock, legality, page
profile, color-mode, checksum, and artifact-signature verification; physical
printer/device certification remains external acceptance work.

Rule-profile consistency addendum — 2026-08-29: draft validation now uses the
selected profile's player-count contract, including 5-on-5 flag designs and
configured youth formats, and prevents the legacy tackle-football line rule
from firing on flag designs. Advanced legality remains explainable and
fail-closed where a local adoption rule source is missing. This is a local
correctness improvement, not evidence of complete NFL/NCAA/NFHS/youth/flag
rulebook coverage; authoritative adoption, officiating review, and deployment
testing remain open.

Asset catalog integrity addendum — 2026-08-29: the palette registry gate now
requires all 13 authoring families and rejects missing replacement targets or
malformed compatibility metadata. The 128-asset canonical catalog passes this
contract; organization-scale catalog governance and deployment validation
remain open.

Atomic concurrent-save addendum — 2026-08-29: expected-revision Play Designer
saves now use a repository-level compare-and-swap boundary in both the JSON and
SQLite adapters. The check and write execute under the adapter's lock, and a
stale writer receives the server snapshot and explicit expected/actual
revisions. A two-editor API race rehearsal passes for both adapters and proves
exactly one 201 winner, one 409 conflict, and a final persisted design matching
the winner. This strengthens the local convergence contract; multi-process
deployment concurrency, network partitions, and production database behavior
remain deployment acceptance work.

Independent-connection addendum — 2026-08-29: SQLite compare-and-swap now
opens an `IMMEDIATE` writer transaction before reading the revision. A new
rehearsal uses two independent SQLite connections against the same database and
proves that one worker commits revision 2 while the stale worker receives a
structured conflict, with no lost update. This is database-level local
evidence; production database topology, lock/timeout tuning, and distributed
multi-region behavior remain deployment acceptance work.

Alternate-path contract addendum — 2026-08-29: the route inspector now exposes
branch-specific family, break, stem depth, break depth, finish direction, and
option-rule controls. Changes use a dedicated branch construction helper that
keeps the selected alternate polyline and semantic contract synchronized while
preserving the primary path. Focused geometry and inspector tests verify the
branch remains independently executable; multi-coach review and production
browser certification remain open acceptance work.

Alternate-path validation addendum — 2026-08-29: server-side structural
validation now requires every alternate path to carry a unique non-empty id,
coach-facing label, and non-empty decision condition, in addition to its
bounded two-point geometry and route semantics. Duplicate branch identities and
missing teaching conditions are now explainable findings before save/review.

Alternate-path collision parity addendum — 2026-08-29: advanced server legality
validation now evaluates route-collision corridors across every primary and
alternate route polyline. Findings identify the exact branch path, expose both
path labels, preserve intentional-crossing documentation requirements, and keep
the route-collision policy behavior consistent with the editor's collision
engine. A regression test verifies a collision that exists only on an alternate
path; browser, multi-user, and production-scale acceptance remain open.

Branch-aware playback addendum — 2026-08-28: branch-specific timeline events
now resolve one executable alternate polyline for the animated ball, player
marker, and active event indicator. The selected branch uses its own event
timing window for progress interpolation, while designs without a branch cue
retain primary-path behavior. This prevents choice routes from animating every
option simultaneously and keeps the teaching view synchronized with the
coach-authored decision cue. Full browser/device animation QA remains open.

Branch-aware timeline contract addendum — 2026-08-28: server timeline
validation now requires every `branch_id` event to reference its owning route
element and an existing alternate branch. When branch timing is authored, the
event must overlap that branch window; missing or misaligned references are
reported with exact event paths and warning/error semantics before save or
review. This closes the persistence and renderer contract gap; authoritative
organization rule adoption and production transport testing remain open.

Strict stream recovery addendum — 2026-08-28: the Play Designer event stream
now treats an out-of-order sequence as a replay boundary. The client cancels
the current reader and reconnects from the last contiguous cursor, preventing
silent loss of a design mutation; duplicate events remain ignored, and
role-filtered organization streams retain their legitimate non-contiguous
visibility behavior. Focused and full frontend suites cover the decision
contract; network fault-injection and multi-browser convergence remain open.

Offline outbox integrity addendum — 2026-08-28: collaboration queue writes,
acknowledgements, and retry-attempt evidence now fail visibly when encrypted
storage cannot persist them. Queue flushing also stops at the first failed
action, preserving causal order so later staff actions cannot overtake an
uncertain earlier mutation. The UI reports that synchronization is paused at
the failed action; browser quota, crash recovery, and production transport
fault-injection remain open.

Rule-profile adoption addendum — 2026-08-29: high-school and youth legality
profiles now require an explicit local rulebook or organization adoption
reference even when no local constraint overrides are supplied. Previously,
the adoption warning was only emitted after an overrides object was present,
which could make an unresolved local profile appear more authoritative than
the available evidence supported. The correction is covered for both profiles
and remains an authoring warning pending program-owner rule adoption; it does
not claim complete jurisdictional rule coverage.

Export drawing-semantics addendum — 2026-08-29: SVG artifacts now preserve
the authored arrow-end contract from the live designer. Start, finish, both,
and no-arrow modes are emitted as matching marker attributes, including on
alternate route branches, so a shared or printed vector cannot silently add a
finish arrow or remove an intentional start arrow. This closes a local
renderer parity defect; PDF/raster device certification and production print
validation remain open acceptance work.

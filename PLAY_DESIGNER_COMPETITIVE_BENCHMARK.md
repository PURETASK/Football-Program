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
| Formation/alignment | 13 professional 11-player presets plus field translation implemented | Add huddle/shift sequences, explicit eligibility, spacing dimensions, and role constraints |
| Assignment graph | In implementation | Structured references, cycle/conflict validation, graph summary, and inspector controls |
| Timeline | Basic synchronized playback exists | Multi-track phases, speed, cue stepping, pauses, narration, exchanges, and ball events |
| Live checks | Saved-design legality exists | Debounced, non-persisting validation of the current unsaved draft |
| Templates/play families | Basic templates exist | Partial-play stencils, variants vs. looks, inheritance, naming, and batch generation |
| Collaboration/versioning | Presence, comments, events, snapshots, branching, diff, merge exist | Shared cursors/thread depth, conflict visualization, release locking, and rollback UX |
| Teaching | Basic role views and mastery records exist | Full player animation, progressive reveal, accessible text, quizzes, and practice links |
| Exports | Server export foundation exists | Visual fidelity, grids, install/scout formats, true wristband layouts, and render QA |

## Definition of done for this workstream

This priority is complete only when all ten capability areas are implemented, connected to organization-scoped persistence, covered by backend and frontend tests, verified in the production bundle, exercised through tablet and keyboard workflows, checked for screen-reader and contrast behavior, traced into the Master Codex audit, and supported by a coach-facing tutorial. Competitive research alone, static mockups, or isolated controls do not satisfy completion.

## Implementation addendum — 2026-08-25

The benchmark is now an active engineering standard, not a research-only note. The latest React slice adds an organization-backed concept-template registry with eight offense/defense starter packages, compatibility-aware palette integration, relative geometry materialization, layer application, and save-current-play template capture. Pre-snap motion is preserved from -5,000 ms and timeline event aliases are normalized into canonical ball, shift, motion, exchange, read, rotation, and pause events.

Version review now returns the immutable base and compare designs alongside element-level diff data. The Review panel can toggle a non-interactive field overlay with dashed compared paths, ghost personnel, and an accessible legend; this keeps review evidence visible on the same field as the active draft. The teaching surface now renders the filtered role/position-group diagram, dims context players, progressively reveals authored steps, and replays the active assignment with accessible play/pause/replay controls.

Verification for this addendum: the full frontend suite passes 116 tests across 27 files; the focused Play Designer service/API/export suite passes 23 tests; TypeScript typecheck passes; and the production build passes with the Play Designer route chunk at 89.48 kB, below the local 90 kB designer ceiling. Remaining benchmark gaps are still active: true multi-user edit convergence, partial-play stencil inheritance and batch variants, production-grade export layout coverage, complete rule-profile depth, automated visual/screen-reader/tablet traces, and moderated pilot evidence.

The export slice now adds a source manifest and manifest hash to every generated artifact. Each manifest records the selected design IDs, versions, immutable snapshot IDs, content checksums, renderer versions/checksums, status, release IDs, and approval state; signed exports include the manifest hash in their HMAC-covered fields. The export dialog shows this source lock before download so a packet can be traced back to the exact canonical play revision used to render it.

The export dialog also exposes audience selection for coach/staff, player, and position-group views. Role-filtered artifacts reuse the canonical visibility rules used by teaching views, so a player packet can be focused without creating a second unsynchronized play record.

Wristband delivery now supports validated standard two-column, compact three-column, and four-column sideline-strip layouts. Each layout has explicit capacity, card width, typography, and truncation rules, and non-wristband artifacts cannot request wristband layouts.

Export preflight addendum (2026-08-26): the export workflow now has a non-rendering `POST /v1/playbook/designs/export/preflight` check. It resolves the same effective layout used by the renderer, validates every organization-scoped source design and audience role, returns explainable warning/error issues, and computes the source manifest hash before content generation. The React dialog requires a fresh matching preflight after any packet, format, layout, or audience change and keeps artifact generation locked while blockers remain. Preflight responses intentionally contain no rendered content, and the final artifact still revalidates before signing.

Install handout addendum (2026-08-26): PDF install-sheet output now uses a dedicated coaching layout with a branded header, canonical field diagram, assignment ledger, player/position ownership, landmark and timing cues, and teaching notes. It preserves role filtering and black-and-white rendering, while CSV remains available for downstream roster or install-card workflows.

Position authoring addendum (2026-08-26): selecting one player icon in the designer inspector now opens a position-aware toolkit backed by the canonical asset registry and concept-template library. Quarterback, offensive-line, backfield, eligible-receiver, defensive-front, linebacker, and secondary profiles rank compatible route, motion, run, blocking/protection, coverage, rush, stunt, fit, read, check, and teaching actions; each option displays an accessible description and timing guide, activates the existing draw tool, and preserves the normal undo/save path. The toolkit also suggests unit- and role-relevant reusable template layers that can be inserted directly into the current call. Frontend verification now passes 125 tests across 30 files, TypeScript typecheck passes, and the production build passes.

Visual authoring addendum (2026-08-26): assignment inspection now includes explicit arrow/line meaning, no-arrow mode, end/start/both/none arrowheads, smooth versus sharp path geometry, solid/dashed/dotted treatment, line-weight, and line-cap controls. The selected path renders those choices on the canonical SVG canvas and continues to animate against the same timeline path. This keeps route, block, motion, run, coverage, rush, stunt, and annotation semantics legible in both live editing and playback; the production build and 125-test frontend suite remain green.

Action materialization addendum (2026-08-26): position recommendations now offer a separate one-click “Add starting action” control in addition to manual draw mode. The new materializer generates bounded, position-relative geometry for routes, motions, runs, blocks/protections, coverage, rushes, stunts, fits, and fallback actions; links the new element to its player and registry asset; applies timing, pre-snap/post-snap phase, landmark, depth, assignment, teaching, arrow, and line metadata; and returns the element through the normal editor reducer for selection, undo, save, version, validation, collaboration, and export. Motion actions are automatically placed on the negative pre-snap timeline. Pure materialization behavior is covered by dedicated tests.

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
edit convergence under concurrent mutations, partial-play stencil inheritance
with persisted batch variants against multiple looks, complete provider-grade
export layout/device certification, authoritative depth for every supported
rule profile, automated browser visual/screen-reader/tablet traces, and
moderated coach/coordinator/player pilot evidence. These items must not be
marked complete from static controls or local unit tests alone.

Repository verification for this reconciliation: the frontend suite passes
163 tests across 42 files, the Python suite passes 598 tests, TypeScript
typecheck and the production build pass, and GitHub Actions validates the
master-plan audit plus the production-configured container runtime. Those
results prove the local and CI foundation; they do not prove production
deployment, real organization adoption, or owner approval.

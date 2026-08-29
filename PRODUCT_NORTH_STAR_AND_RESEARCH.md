# Product north star and play-design research

Updated: 2026-08-29

## The main thing this app is

NFL FIDOS is a coach decision-to-delivery operating system. Its primary job is
to help a football staff turn evidence into an approved, teachable, executable
decision:

**Decide -> design -> validate -> teach -> practice -> observe -> adjust -> release.**

The Play Designer is the central structured object in that loop, but it is not
the whole product. A play must remain connected to roster roles, film evidence,
practice reps, player learning, game-plan approval, delivery packets, and
outcomes. Today should make the next decision obvious; each workspace should
complete one part of the loop; the backend remains the authority for scope,
approval, persistence, and audit history.

## Research reviewed

- [FirstDown PlayBook](https://firstdown.playbooktech.com/) emphasizes a large
  editable professional catalog, offense/defense/special teams coverage,
  reusable partial-play stencils, multiple field formats, lineman view,
  mirroring, practice schedules, and wristband outputs.
- [Hudl Play Tools](https://www.hudl.com/products/playtools) emphasizes
  formation/play/front templates, attached video, drawings and notes, targeted
  install sharing, study activity, film-linked practice scripts, and offline
  access.
- [GoRout Connect](https://gorout.com/connect/) demonstrates the value of a
  design-to-practice handoff: drawings should move into practice blocks and be
  visible to players without rework or manual file organization.
- [Football Playbook](https://footballplaybook.com/) highlights a simpler
  touch-first editor with player placement, routes, motion, animation speed,
  and multi-page PDF export.
- [Hudl's play-add tutorial](https://www.youtube.com/watch?v=H2SB289uOzI)
  shows a coach-friendly sequence: add a play, choose formation, attach film,
  choose a defensive front, add drawings/notes, and set field settings.

## Capabilities to preserve in our own implementation

1. A fast mode-based canvas: select, player, route/path, block, motion, run,
   coverage, rush, annotation, erase, pan, and zoom.
2. Reusable assets at three levels: full play templates, partial concept or
   protection stencils, and atomic route/block/motion symbols.
3. Player-aware authoring: selecting a player should rank compatible actions,
   explain why they fit the position and phase, and materialize a bounded
   starting action that stays editable.
4. Defensive parity: fronts, techniques, gaps, fits, cover shells, rotations,
   pressures, stunts, exchanges, and replacement responsibilities should be
   authored with the same depth as offensive routes.
5. Teaching controls: line-of-scrimmage and lineman views, role filtering,
   progressive reveal, timing cues, narration, quizzes, and player-safe output.
6. Delivery controls: mirror and variant creation, practice linkage, install
   packets, call sheets, wristbands, PDFs, SVG/PNG, print profiles, and
   immutable release manifests.
7. Evidence and governance: source clips, notes, validation findings,
   organization terminology, approval state, version history, checksums, and
   explicit human overrides remain visible.

## UX decision

The application now exposes a universal workspace tutorial launcher on each
non-designer workspace and an explicit **Operating lens** control. The default
lens is Head coach; coordinator, position coach, analyst, and player-facing
perspectives can be selected for guidance and filtering. This is a user-facing
scope preference only: it never grants access or changes server authorization.
The dedicated Play Designer retains its own deeper tutorial because its canvas,
inspector, timeline, teaching, review, and export controls need contextual
instruction.

## Boundaries

This research is a capability benchmark, not a license to copy another
product's code, artwork, protected brand identity, or trade dress. The product
must use original implementation and organization-controlled terminology while
matching useful workflow outcomes.

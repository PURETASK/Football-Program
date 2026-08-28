# Professional Play-Creation System Research

## Findings

The system needs a canonical play model, not a freehand image. The model must
represent personnel, formation, alignment, assignments, routes, blocks, run
paths, motion, reads, defensive front, coverage, pressure, fits, rotations,
timing, call words, provenance, and approval. The UI can then render coach,
quarterback, position, tablet, mobile, print, and animation views from the same
record.

The NFL rulebook is the source of truth for legality checks. The offense must
have at least seven players on the line, eligible receivers at both ends, and
motion must be parallel to or away from the line of scrimmage at the snap; a
backfield player moving under/behind center must stop for one full second before
the snap. These constraints belong in a linting layer, while team-specific
rules remain configurable.

Public coaching material supports a reusable vocabulary of formations,
personnel, route concepts, and motion. USA Football examples show formation
families such as spread, trips, stack, double-back, I, and single-back, and
describe motion as a way to change strength, create misdirection, or stress the
edge. Defensive diagrams need independent front, stunt/blitz, and coverage
layers: a front defines gap/technique structure; rush and stunt paths define
pressure; coverage and fit assignments define the secondary and run response.

Commercial playbook products consistently expose reusable formation/route
templates, player movement, motion, annotations, animation, roster/library
management, sharing, PDF export, wristbands/call sheets, and practice/install
linkage. These are product requirements, not football rule claims.

## Canonical feature inventory

### Offensive authoring

- personnel and formation templates; strength, field/boundary, splits, stance
- route types: vertical/go/fade, seam, post, corner, out, dig, curl,
  comeback, slant, drag/over, whip/pivot, wheel, angle, flat, swing, screen,
  choice and stop
- stem/release, landmark/depth, break angle, leverage, tempo, settle rules
- run track, aiming point, blocking scheme, combo/pull/trap, protection slide,
  scan, release, hot and checkdown responsibilities
- motion and shifts with start/end positions, timing, return/jet/orbit/fly/zip,
  reset state, snap relationship, and defensive adjustment
- quarterback progression, alert, conflict defender, coverage key, cadence,
  kill/check words and situational tags

### Defensive authoring

- personnel/package, front, shade/technique, box count, gap/run-fit and force/
  spill/contain responsibilities
- man, zone, match, bracket, and prevent coverage families; shell, leverage,
  landmarks, checks, communication and motion adjustment
- rush lanes, blitz paths, green-dog/spy/drop, line games, stunts/twists,
  exchanges, simulated pressure and rotations
- pre-snap disguise, post-snap rotation, read keys and assignment conflicts

### Rendering and workflow

- field grid with line of scrimmage, hashes, sidelines, end zones and optional
  first-down marker; coordinate-accurate points and snap timeline
- consistent line semantics: solid route/run arrows, dashed pre-snap motion,
  red pressure arrows, bars for blocks, arcs for zones, numbered reads, and
  check diamonds; every mark needs a text equivalent for accessibility
- layers, undo/redo, snap-to-landmark, route handles, templates, version diff,
  what-if overlays, role views, animation, print/PDF, wristband and call-sheet
  exports, plus library/search/tagging by formation, concept, situation and
  coverage
- linting for structural completeness, duplicate/missing players, coordinate
  bounds, route/path integrity, motion legality, formation eligibility,
  assignment completeness, defensive fit/coverage conflicts, provenance and
  approval state

## Sources

- NFL Operations, [2026 NFL Rulebook](https://operations.nfl.com/rules-officiating/2026-nfl-rulebook)
- NFL Operations, [Formations](https://operations.nfl.com/rules-officiating/nfl-football-basics/formations)
- NFL Operations, [Football Terms](https://operations.nfl.com/rules-officiating/nfl-football-basics/football-terms)
- USA Football, [Introduction to Formations](https://assets.usafootball.com/documents/rookietackle/resources/ADM-Playbook-Flip-Charts-Flag-Spread-Trips-Stack_Flag.pdf)
- USA Football, [Formation and motion concepts](https://blogs.usafootball.com/blog/956/3-specific-ways-to-believe-in-your-athlete)
- Football Playbook Designer, [feature inventory](https://www.footballplaybookdesigner.com/features.html)
- PlayMaker, [editor/database/animation capabilities](https://www.playmaker.com/software/playmaker-football-windows)
- FirstDown PlayBook, [templates and play-drawing features](https://firstdown.playbooktech.com/)

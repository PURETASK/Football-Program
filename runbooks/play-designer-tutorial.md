# Play Designer in-app tutorial

The React Play Designer includes a contextual, eight-step tutorial. It explains the workspace without changing the open play, submitting a review, publishing, branching, or generating an export.

## Start or restart the tutorial

1. Open `/app/playbook/designer/:designId` or `/app/playbook/designer/new` with an authorized organization session.
2. The tutorial opens automatically until that browser profile has completed it.
3. Select the `Tutorial` help control in the designer toolbar to restart it at any time.
4. Use `Close tutorial` or `Escape` to dismiss it. Dismissing does not mark it complete.
5. Select `Finish tutorial` on step eight to record completion in local browser preferences.

The preference contains only the tutorial-completion flag. Organization credentials remain in tab-scoped session storage, and canonical football records remain on the Python API.

## Tutorial sequence

### 1. Build a complete football call

Explains the core operating model: the Python API is canonical, every visual object has football metadata, and controlled state changes remain human authorized.

### 2. Start with the professional asset library

Introduces formations, routes, motions, runs, protections, fronts, coverages, pressures, checks, and teaching annotations. It explains category filters, compatibility filtering, and tool activation.

### 3. Author and edit on the field

Introduces the canonical 100-by-53 field, player movement, drag-to-draw paths, route handles, keyboard nudge, and multi-selection.

### 4. Control the editing workflow

Explains Select, Pan, Route, Motion, history, duplicate, mirror, group, delete, snapping, staff presence, review, export, and save state.

### 5. Teach timing and movement

Explains synchronized playback, scrubbing, assignment timing windows, player movement, route phases, and teaching markers.

### 6. Add the football details

Explains the four inspector panels:

- `Inspect` edits play identity, alignment, assignment metadata, timing, and visibility.
- `Layers` controls selection, visibility, and locks.
- `Checks` reports legality and structural findings with explanations.
- `Review` contains staff comments, decision controls, branching, and immutable history.

### 7. Save, review, publish, branch, and export

Explains autosave revisions, explicit conflict recovery, human decision references, publish controls, branch creation, immutable history, and validated export evidence.

### 8. You are ready to build

Summarizes the recommended call-building sequence: establish personnel and formation, create assignments, teach timing, run checks, and request review.

## Contextual descriptions in the designer

The tutorial is supplemented by permanent, visible descriptions:

| Region | Description provided |
| --- | --- |
| Asset library | What can be searched, how compatibility works, and how an asset activates authoring |
| Field canvas | What can be drawn, selected, positioned, and taught on the shared field |
| Timeline | What is synchronized and how timing supports teaching |
| Inspect | What metadata can be edited without redrawing |
| Layers | How visibility, locking, ordering, and selection are managed |
| Checks | What validation means and how findings are explained |
| Review | How comments, decisions, versions, publishing, branching, and exports are controlled |

## Keyboard behavior

- `Escape` closes the tutorial.
- `Right Arrow` advances when another step exists.
- `Left Arrow` returns to the prior step.
- `Tab` reaches progress controls, Close, Back, and Next or Finish.
- The current Next or Finish control receives focus when a step opens.
- The highlighted workspace region remains usable because the tutorial is nonmodal.

## Verification contract

Automated frontend tests verify opening, named content, step advancement, completion, and Escape dismissal. Integrated browser QA verifies the first-time flow, Review-panel synchronization, completion persistence, toolbar restart, desktop rendering, and the 820-pixel tablet layout. Python HTTP tests verify direct designer refresh and successful delivery of the lazy designer JavaScript and shared stylesheet assets.

The tutorial is instructional evidence only. It does not constitute staff training acceptance, moderated pilot evidence, owner approval, or production authorization.

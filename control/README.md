# Program Control Plane

This directory is the executable Stage 0 control plane for the NFL Football Intelligence & Development OS.

## Artifacts

- `manifest.json` — program state, source authority, stage sequencing, and identifier rules.
- `stage-manifest.json` — the full Stage 0–25 roadmap with current implementation status.
- `stage-0a-registry.json` — the initial capability, agent, object, workflow, nuance, risk, and question registry.
- `stage-0-exit-gate.json` — explicit Stage 0 exit checks. Checks remain open until discovery and owner review are complete.
- `schemas/registry.schema.json` — structural contract for registry records.

Validate from the repository root with:

```text
python scripts/validate_control_plane.py
```

When the uploaded source artifacts are mounted, run the source-to-repository
conformance audit as well:

```text
python scripts/audit_master_plan.py
```

The audit checks all 26 roadmap stages, required deliverables, DOCX stage
heading parity, and traceability evidence paths. It does not grant owner
approval or enable production implementation.

Stage 0 owner approval evidence is governed by
`contracts/stage-0-owner-approval.schema.json` and can be prepared from
`control/stage-0-owner-approval-template.json`. Approval records are
non-activating: they do not modify the stage manifest or enable production.

The validator is intentionally dependency-free and checks stable IDs, required metadata, references, duplicate IDs, and the Stage 0 gate status.

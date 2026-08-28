# Project Audit Checkpoint

Run `PYTHONPATH=src python scripts/project_audit.py` to compose the current project checkpoint from the checked-in Markdown/DOCX conformance audit, traceability evidence validation, deterministic evaluation suite, and Stage 0 control manifest. The source artifacts live under `governance/master-plan/`; a local Downloads copy is supported only as a fallback.

To retain the exact machine-readable checkpoint for an owner-review or CI evidence bundle, add `--output`:

```powershell
$env:PYTHONPATH = (Resolve-Path '.\\src').Path
python scripts/project_audit.py --output .\\runtime\\project-audit-latest.json
```

The output is written only to the requested local path and is also reported in
the command result as `evidence_output`. Persisting the report does not record
approval, advance a stage, enable production, or change an external system.

To compose the project audit with the React feature-parity and browser-evidence
validators in one review artifact, run:

```powershell
$env:PYTHONPATH = (Resolve-Path '.\\src').Path
python scripts/build_local_evidence_bundle.py `
  --output .\\runtime\\local-evidence-bundle.json
```

The bundle is valid only when every included check passes. It always preserves
non-activating safety flags and does not replace owner approval, deployment
evidence, or moderated pilot evidence.

The command reports `foundation_verified` only when those checks pass. It always reports remaining stage work and sets `completion_claimed=false`; it cannot record owner approval, advance the stage, enable production, deploy services, or substitute for real organization/provider/pilot evidence.

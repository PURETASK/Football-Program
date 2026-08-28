# Stage 0 Owner Approval

The Stage 0 approval surface records explicit, authenticated program-owner evidence against the evaluated registry and exit gate. It is an evidence workflow only: it never edits `control/manifest.json`, advances the stage, enables production, or authorizes deployment.

Use the Governance workspace in `ui/operator-dashboard.html`, or call `POST /v1/control/stage-0-approval` with an organization-scoped `program_owner` token and `approval_id`, `rationale`, `evidence_refs`, and an ISO-8601 `approved_at` value. The service evaluates the current registry and gap audit before accepting the record. If the gate is not `ready_for_approval`, the request is rejected.

Use `GET /v1/control/stage-0-approval?organization_id=...` to inspect the current gate and organization-scoped approval evidence. A valid record is not sufficient by itself to advance the stage; the control-plane manifest and separate release authorization remain human-governed.

Before requesting owner action, run `python scripts/stage0_owner_approval_preflight.py`. It produces a value-free review packet with the evaluated gate, required evidence references, and an approval payload template. The command never records approval, edits the manifest, advances the stage, or enables production.

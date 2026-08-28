# Pilot Organization Selection

Use `POST /v1/delivery/pilot-organization` or the dashboard Pilot Organization Selection workspace to select an organization for a named MVP wave. The organization must already have an active context and an approved terminology bundle. The request requires a program-owner token, complete pilot role coverage, and a `DEC-*` decision reference.

The resulting `PILOT-SEL-*` record is an auditable selection artifact. It does not start a live pilot, send data, enable feature flags, advance the stage, or authorize production deployment. Inspect selections with `GET /v1/delivery/pilot-organization?organization_id=...`; use the separate pilot-readiness gate for acceptance evidence, rollback, and owner approval.

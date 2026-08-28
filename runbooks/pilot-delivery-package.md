# Pilot Delivery Package

Use `POST /v1/delivery/pilot-package` to compose a selected organization, a `ready_for_pilot` readiness report, and a passed rollback result into a `PILOT-PKG-*` record. The endpoint is program-owner-only and requires all identifiers to remain organization- and wave-scoped.

The package is a bounded release handoff, not activation. It reports `live_pilot: false`, `production_implementation_allowed: false`, and `external_state_changed: false`. Failed readiness, mismatched scope, enabled feature flags, or failed rollback block package creation. Inspect saved packages with `GET /v1/delivery/pilot-package?organization_id=...`.

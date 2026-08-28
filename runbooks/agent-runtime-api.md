# Agent runtime API rehearsal

`POST /v1/agents/runs` is an authenticated, organization-scoped dispatch surface for local validation only. It requires `program_owner` or `validator`, `local_validation: true`, a controlled agent-bible role/capability, and a non-empty `RUN-*`/`WF-*` request. The route registers the deterministic local adapters, activates only for the bounded validation request, and persists the auditable run under the caller's tenant.

`GET /v1/agents/runs?organization_id=...` returns only runs visible to the authenticated organization. Responses explicitly report `external_provider_called: false`, `canonical_write_performed: false`, and `production_implementation_allowed: false`. Provider credentials, model adapters, canonical publication, and production activation remain outside this rehearsal boundary.

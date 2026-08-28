# Organization population readiness

`GET /v1/organizations/population-readiness?organization_id=ORG-...&season=...` reports whether the tenant has the thirteen persisted components required by the organization operating bundle. It resolves only the caller's organization, reports the required versus actual state for each package, and exposes blockers without creating or upgrading records.

The checklist is intentionally non-activating: it does not mark data validated, approve an organization, advance Stage 0, call a provider, or enable production. A `ready_for_bundle` result means the persisted records meet the bundle's state checks; it still requires the separate operating-bundle submission and human owner review.

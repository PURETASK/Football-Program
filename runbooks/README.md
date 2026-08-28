# NFL FIDOS Operational Runbooks

These runbooks are operator procedures for the local and validation runtime. Production execution requires an approved organization context, authorized credentials, and the applicable human owner.

- `failed-eval.md` - stop promotion, preserve evidence, triage, rerun.
- `permission-denial.md` - inspect scope and role, never bypass a denial silently.
- `source-freshness.md` - review stale evidence and preserve citations.
- `schema-migration.md` - dry-run, snapshot, migrate, verify, rollback.
- `media-ingestion.md` - validate authorization, roots, format, digest, and QA.
- `audit-inspection.md` - inspect append-only events and approval links.
- `incident-escalation.md` - contain, preserve, notify, and review safety/security events.
- `demo-seed-data.md` - create, explore, inspect, and safely remove the synthetic showcase tenant.
- `frontend-migration.md` - build, verify, operate, and continue the React interface migration without removing legacy workflows early.

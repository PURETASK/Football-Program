# Organization Staff Review Runbook

This workflow records organization-scoped staff roles and observable coaching evaluations against the controlled NFL coaching-staff architecture. It does not infer employment, credentials, medical status, personality, or private personnel facts.

Coaching staff submit `POST /v1/staff/organization-review` with team context, season, staff records, and optional evidence-linked evaluations. Valid packages remain `under_review`. A program owner may use `POST /v1/staff/organization-review/approve` with a DEC-* or APPROVAL-* reference to record validation. Approval does not publish staff doctrine, change permissions, advance a stage, or enable production.

Every evaluation must cover the controlled dimensions for the person’s role and include observable evidence. Invalid roles, incomplete dimensions, invalid ratings, or missing evidence are rejected.

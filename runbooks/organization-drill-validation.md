# Organization Drill Validation Runbook

## Purpose

Create an organization-scoped package that selects validated base or seasonal drills for a position and season, links them to authorized source references, and holds the package for human review.

## Process

An authenticated coach or validator submits `POST /v1/practice/drill-validation`. The service checks the selected IDs against the controlled base and seasonal corpora, enforces organization and position scope, and stores the package as `under_review`. Governance users inspect packages with `GET /v1/practice/drill-validation?organization_id=...`.

A program owner may submit `POST /v1/practice/drill-validation/approve` with the package ID and a `DEC-*` or `APPROVAL-*` decision reference. Only this explicit owner action transitions the package to `validated`.

## Safety boundary

The package does not prescribe medical activity, change a player plan, or activate production. Validation is an auditable content decision only; it does not advance a stage or enable production.

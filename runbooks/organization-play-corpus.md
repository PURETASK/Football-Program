# Organization Play Corpus Runbook

## Purpose

Compile organization-scoped play records against the deterministic play compiler, preserve source references, and hold the resulting corpus for explicit human review.

## Process

Coaching staff submit `POST /v1/playbook/organization-corpus` with organization/team/season context, source references, and play records. The service stores only compiler-validated packages as `under_review`. A program owner may use `POST /v1/playbook/organization-corpus/approve` with a decision reference to transition a valid package to `validated`.

## Safety boundary

The compiler validates structural invariants; it does not prove a private team doctrine or football legality in every system. Approval does not publish plays, advance a stage, or enable production. Organization-specific doctrine and authorized source evidence remain required.

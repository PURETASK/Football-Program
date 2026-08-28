# Usability Feedback Runbook

## Purpose

Capture role-scoped pilot and deployment usability evidence for dashboard tasks, including task outcome, severity, accessibility findings, and supporting evidence references.

## Process

An authenticated user submits `POST /v1/ux/usability-feedback` with an `UX-FEEDBACK-*` ID, `UX-SESSION-*` session, screen/task identifiers, outcome, severity, feedback text, timestamp, and evidence reference. The server derives the user role and organization from the authenticated principal. Governance roles inspect feedback with `GET /v1/ux/usability-feedback?organization_id=...`.

Blocked tasks, major/critical findings, and accessibility issues require human review. Submission does not alter permissions, release flags, stage state, or production configuration.

## Safety boundary

This workflow records evidence only. It does not claim pilot completion, replace deployment-environment testing, or automatically accept/reject a UX change.

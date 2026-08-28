# Organization Scouting Package Runbook

This workflow composes an organization-scoped opponent profile, situational reports, matchup models, and evolution warnings from explicitly supplied authorized-source references. It does not fetch live sources, infer private opponent information, or guarantee future behavior.

Analysts submit `POST /v1/scouting/organization-package`. The package remains `under_review` until a program owner validates it with a DEC-* or APPROVAL-* reference. Source references on every report must be listed in the package source set. Approval records review evidence only; it does not publish a game plan or enable production.

# Organization Player Development Runbook

This workflow creates organization-scoped individual development plans and mastery evidence for NFL players. It preserves evidence, measurable objectives, review ownership, and privacy boundaries; it does not make medical, clearance, or employment decisions.

Coaching staff submit `POST /v1/player-development/organization-package` with player identifiers, position context, objectives, and optional mastery records. The package remains `under_review` until a program owner validates it with a DEC-* or APPROVAL-* reference. Production and stage advancement remain disabled.

Coaches and program owners may inspect the team package. A player may request only their own filtered record using `player_id` equal to their authenticated subject. Team-level interpretation remains staff-controlled.

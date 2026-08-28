# Organization Weekly Game-Plan Runbook

This workflow compiles an organization-scoped weekly game plan with offense, defense, special teams, situational plans, matchups, contingencies, ownership, and player teaching outputs. It preserves evidence, trigger ownership, counter-counter logic, and human decision authority.

Coaching staff submit `POST /v1/game-plan/organization-package`. The compiled package remains `under_review` until a program owner validates it with a DEC-* or APPROVAL-* reference. Validation does not publish the plan, create external operations, or enable production; release remains separately governed by the weekly-delivery and pilot gates.

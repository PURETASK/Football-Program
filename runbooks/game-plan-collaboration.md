# Game Plan Collaboration

The authenticated game-plan collaboration routes provide organization-scoped review threads, evidence-linked comments, and explicit decisions for weekly staff coordination:

- `GET /v1/game-plan/threads?organization_id=ORG-...`
- `POST /v1/game-plan/threads`
- `POST /v1/game-plan/threads/comments`
- `POST /v1/game-plan/threads/resolve`

Every thread and comment requires evidence references. Resolving a thread requires a `DEC-*` decision record and rationale. A resolved discussion records staff review evidence; it does not publish a game plan, bypass a release gate, or enable production.

# Media retention planning

`GET /v1/media/retention-plan` exposes an owner-scoped, non-destructive review report. Assets with valid timestamps older than the policy are candidates; missing timestamps remain `unknown` and are never treated as expired. The planner does not delete or mutate media. Any cleanup requires a separate approved change and retention evidence.

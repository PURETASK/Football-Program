# Managed Media Retention Execution

`execute_media_retention` is the separate execution boundary after the retention planner and scan. It defaults to `execute=False`, requires a `program_owner` actor and explicit `approval_ref`, rejects unknown timestamps, and only considers regular files inside the supplied managed storage root. The asset record is retained as an auditable tombstone after a successful file deletion.

Validation execution may be rehearsed against a temporary managed root. Production execution additionally requires `production_implementation_allowed=true` from the controlled Stage 0 manifest. The existing retention plan and scan remain non-destructive; this executor is used only after the applicable owner-approved retention decision.

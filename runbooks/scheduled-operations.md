# Scheduled operations

External schedulers should invoke `scripts/scheduled_operations.py` with an organization, actor, worker ID, and explicit bounds. The command plans by default and emits JSON evidence. `--execute` is required to run source refresh, retention scans, and media transforms; production execution is blocked until the Stage 0 control manifest explicitly permits production implementation.

Persist the JSON result and treat `partial_failure` or `blocked` as an operator event requiring review. Never remove the bounds or bypass the source allowlist, retention review, or media worker path controls.

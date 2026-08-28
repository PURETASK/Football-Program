# Deployment runtime rehearsal

Run `python scripts/deployment_runtime_rehearsal.py` to exercise the actual standard-library HTTP adapter, dashboard serving, control-plane response, deterministic evaluation endpoint, malformed-request boundary, unknown-POST boundary, SQLite creation, and database reopen path in a temporary workspace.

The rehearsal is local and non-activating. It does not deploy a container, register external providers, use production secrets, enable production, or change external state. A passing rehearsal is deployment evidence, not Stage 0 approval.

# Operational readiness

Run the non-destructive readiness check before a validation or deployment operation:

```text
set PYTHONPATH=src
python scripts/readiness_check.py
```

The report checks runtime configuration, database parent writability, SQLite integrity, migration currency, the evaluation suite, and the controlled Stage 0 manifest. A `blocked` result is evidence for remediation, not permission to bypass a gate. Production remains disabled until the Stage 0 owner-approval gate is explicitly closed.

Production may source authentication from `NFL_FIDOS_AUTH_SECRET_FILE`, which should be mounted by the approved secret manager. Readiness also verifies that the structured observability path is writable; external monitoring adapters must consume bounded structured events through the provider-neutral observability sink.

The monitoring contract is defined in `monitoring/observability-contract.json`. Run `python scripts/incident_rehearsal.py` for a bounded local failure/recovery rehearsal; it creates temporary events only, verifies structured export, and confirms the non-activating rollback contract.

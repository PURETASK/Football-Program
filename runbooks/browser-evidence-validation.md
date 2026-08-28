# Browser Evidence Validation

Run `PYTHONPATH=src python scripts/validate_browser_evidence.py` after a local browser rehearsal. The validator checks that the evidence is Stage 22, passed, tied to a local reference URL, includes the governance/population/agent-runtime and console checks, and preserves the no-external-state, production-disabled, deployment-limited, and pilot-limited boundaries.

This validates the evidence package; it does not replace an actual browser session or claim deployment-environment or pilot-user usability validation.

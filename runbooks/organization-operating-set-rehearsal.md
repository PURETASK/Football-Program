# Synthetic organization operating-set rehearsal

Run `python scripts/organization_operating_set_rehearsal.py` to build the thirteen organization components through their real package builders, apply synthetic owner-validation fixtures, persist them in a temporary tenant-scoped repository, run population readiness, resolve the persisted components, and compose the operating bundle.

The rehearsal is synthetic and non-production. A passing result means the package shapes, status transitions, tenant persistence, readiness checklist, and operating-bundle composition work together. It does not constitute approval for a real organization, does not use live team data, does not call providers, and does not activate production or advance the Stage 0 gate.

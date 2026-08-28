# Source Integration Rehearsal

Run `python scripts/source_integration_rehearsal.py` to exercise the source connector against a temporary loopback HTTP fixture. It verifies real local transport, response hashing, freshness state, persisted refresh evidence, redirect allowlist rejection, and maximum-response-size rejection.

The fixture is synthetic and local-only. The rehearsal does not contact NFL/team sources, use production credentials, fetch external content, mutate external state, or enable production. Production source retrieval remains HTTPS-only, explicitly domain-allowlisted, bounded, and subject to owner/jurisdiction review.

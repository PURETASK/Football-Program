# NFL FIDOS Synthetic Pilot Rehearsal

Run `python scripts/pilot_rehearsal.py` to compose the WAVE-001 evaluation checkpoint, role coverage, acceptance evidence, feature-flag defaults, readiness gate, and rollback simulation.

This is a synthetic rehearsal only. It uses `ORG-SYNTHETIC-PILOT`, does not select a real organization, does not activate production, does not send messages, and does not mutate external state. The synthetic approval reference demonstrates the gate mechanics; it is not program-owner approval for a live pilot.

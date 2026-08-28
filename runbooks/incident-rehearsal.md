# Local Incident Rehearsal

Run `PYTHONPATH=src python scripts/incident_rehearsal.py` to rehearse a bounded observability failure and recovery in a temporary workspace. The rehearsal records one structured error event, one recovery event, exports both through the configured sink adapter, and validates the deployment rollback contract.

This rehearsal does not contact a monitoring provider, deploy or roll back a service, use production secrets, notify stakeholders, or alter external state. Preserve its JSON output as local evidence. A production incident rehearsal still requires the deployment owner, provider monitoring registration, and participating stakeholders.

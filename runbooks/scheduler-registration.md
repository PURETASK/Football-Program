# Scheduler Registration Runbook

## Purpose

Validate the bounded external-scheduler contract before a deployment owner registers jobs with a provider. This preflight does not contact or mutate a scheduler.

## Validation

Run `python scripts/scheduler_registration_preflight.py --environment validation`. For production, provide the deployment-owned `NFL_FIDOS_SCHEDULER_REGISTRATION_REF` and run the same preflight only after the Stage 0 control gate and deployment approvals are complete.

The contract requires provider-neutral jobs, the bounded `scripts/scheduled_operations.py` entrypoint, positive source/transform/retention limits, and dry-run as the default. The scheduled operations command must still receive an organization, actor, worker ID, and explicit bounds.

## Safety boundary

The preflight reports `external_registration_performed: false` and `external_state_changed: false`. Provider-specific registration, licensed source authorization, and production execution remain deployment-owner actions subject to human approval and the Stage 0 gate.

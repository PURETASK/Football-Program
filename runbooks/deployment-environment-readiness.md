# Deployment Environment Readiness Runbook

## Purpose

Compose the deployment contract, secret/control gate, migrated database, evaluation, scheduler, and monitoring checks into one value-free readiness report. This is a preflight, not a deployment command.

## Usage

Run `python scripts/deployment_environment_readiness.py --environment validation --database <migrated-database>` after setting a validation authentication secret and an observability path. The report must show all four component reports as `ready` before a deployment owner proceeds.

Production reports remain blocked unless the external secret source, scheduler registration reference, monitoring registration reference, deployment database, provider tools, and Stage 0 authorization are present.

## Safety boundary

The report always declares `activation_performed: false` and `external_state_changed: false`. It does not migrate a database, register scheduler jobs, register monitoring backends, deploy services, or enable production.

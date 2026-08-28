# Browser Validation Runbook

## Purpose

Validate the served operator dashboard in a local reference environment without activating production, recording owner approval, or creating pilot state.

## Preconditions

- Start the local reference service with the repository's documented authentication configuration.
- Confirm `control/manifest.json` still reports `production_implementation_allowed: false`.
- Use the browser-control workflow against `http://127.0.0.1:8080/`.

## Checks

1. Confirm the dashboard banner, navigation, program status, and governance workspace render.
2. Load Stage 0 gate evidence and confirm the expected authentication boundary when no approved token is supplied.
3. Confirm the Playbook authoring and Game Plan collaboration controls are visible.
4. Confirm the dashboard reports the current stage, evaluation result, and approval state.
5. Submit a deliberately invalid film token and confirm the request is rejected without state creation.
6. Open the Usability feedback workspace, confirm its controlled fields render, and confirm submission without approved organization/token is rejected without state creation.
7. Open the Controlled agent runtime workspace, confirm the local-validation-only warning, and confirm the form requires an organization-scoped owner or validator token.
8. Record the result in `control/browser-validation-evidence.json` and preserve the distinction between local browser validation and deployment/pilot validation.

## Safety boundary

This runbook is read-only with respect to production and pilot systems. It does not record Stage 0 owner approval, advance the stage manifest, enable production, or claim pilot-user usability validation.

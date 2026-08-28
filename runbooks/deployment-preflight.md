# NFL FIDOS Deployment Preflight

Run `python scripts/deployment_preflight.py --environment validation` to produce value-free evidence for the design contract, configured secret source, and Stage 0 control plane. The command does not deploy, activate, migrate, or change production state.

Production preflight intentionally remains blocked until both conditions are true:

1. The authentication secret is supplied through an approved mounted external secret source.
2. The Stage 0 owner-approved control manifest explicitly permits production implementation.

The preflight output contains source type, path/readability metadata, contract issues, blockers, and `activation_performed: false`; it never prints secret values.

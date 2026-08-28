# Provider adapter registration

This boundary certifies the metadata required before a provider-specific adapter can be deployed. It is provider-neutral and does not contact providers.

1. Submit `POST /v1/integrations/provider-adapter` with a read-only provider declaration, approved source/provider reference, capability list, non-secret credential reference, and healthcheck evidence reference.
2. Resolve rejected metadata before review. Credential values, tokens, passwords, write modes, and unapproved capabilities are rejected.
3. A program owner validates with `POST /v1/integrations/provider-adapter/approve` and a `DEC-*` or `APPROVAL-*` reference.
4. Treat a validated registration as deployment evidence only. A separate provider-specific deployment, secret-manager registration, monitoring registration, and Stage 0 authorization are still required.

The workflow never calls an external provider, registers an external service, mutates external state, or enables production.

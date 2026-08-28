# Local agent adapter rehearsal

`register_local_validation_adapters` registers deterministic adapters for the capabilities declared in the controlled agent organization bible. By default it does not activate agents. With explicit rehearsal activation, dispatch returns hashed payload metadata, routing identity, and safety flags only; it does not return payload values, call a model/provider, write canonical artifacts, or enable production.

This is validation evidence for the agent lifecycle and handoff boundary. Provider-specific model/tool adapters, credentials, and production activation remain deployment-owner work.

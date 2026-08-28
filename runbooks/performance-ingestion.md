# NFL FIDOS Performance Ingestion

Performance batches must declare an authorized source kind, source reference, capture time, organization scope, athlete context, observed time, workload, and quality score. The ingestion boundary preserves provenance and privacy scope, rejects medical-decision fields, and marks health signals for qualified staff review.

The ingestion function does not call an external provider, diagnose, recommend treatment, make clearance decisions, or write production data. A production adapter must be separately authorized and must persist the returned batch evidence through the organization-scoped repository.

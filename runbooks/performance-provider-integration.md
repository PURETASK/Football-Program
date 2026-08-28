# Performance Provider Integration

`POST /v1/performance/batches` accepts a bounded, organization-scoped performance batch from an approved provider boundary. The provider must declare an approved kind, `mode: read_only`, and a `SOURCE-*` or `PROVIDER-*` reference.

The endpoint validates and ingests supplied evidence only. It does not contact a provider, make a medical decision, diagnose an athlete, or change external state. Health-related signals remain explicitly subject to qualified performance or medical-staff review.

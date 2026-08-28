# Analytics Provider Integration

`POST /v1/analytics/batches` accepts up to 1,000 provider-supplied metric calculation records. Providers must declare an approved kind, `mode: read_only`, and an approved `SOURCE-*` or `PROVIDER-*` reference matching the source manifest.

The boundary calculates and stores lineage-bearing observations only. It does not contact providers, change external state, authorize generalization beyond the denominator rules, or publish an analytics report. Analysts and coaching staff retain interpretation and review authority.

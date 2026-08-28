# Authorized source refresh

`POST /v1/sources/refresh-all` performs a bounded, organization-scoped refresh of stale registered sources. Every source produces its own refresh evidence; a single failure yields `partial_failure` and `human_review_required` rather than being hidden. The operation does not authorize new domains or promote source content to canonical knowledge.

`POST /v1/sources/scheduled-refresh` calculates due sources from their freshness windows, applies the same source-count bound, executes only the selected stale sources, and persists the schedule/batch report. It is scheduler-ready but intentionally remains an explicit request until a deployment owner supplies an approved external scheduler and production source credentials.

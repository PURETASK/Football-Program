# Media Worker Runner

The bounded runner claims at most 50 queued or retryable jobs per invocation, executes only declared media operations, requires an approved storage root, persists a batch report, and records failures for operator review.

Example:

```powershell
python scripts/media_worker_runner.py --database .runtime/media.sqlite3 --organization-id ORG-TEAM --worker-id MEDIA-WORKER-01 --actor WORKER-OPERATOR --allowed-root C:\approved\managed-media --max-jobs 10
```

The runner never invokes a shell, never processes jobs outside the tenant repository, and never changes external provider state. A `partial_failure` report requires remediation or retry; it is not a promotion signal.

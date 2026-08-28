# Media worker

Media jobs are queued and claimed through the authenticated API. The bounded worker supports `probe` and `index` jobs:

```python
from nfl_fidos.media_worker import process_media_job
```

It requires an approved storage root, never invokes a shell, limits `ffprobe` execution, records output evidence, and completes with `metadata_only` when `ffprobe` is unavailable. `index` records stream metadata and explicit searchable fields for downstream Film search without decoding or publishing media. Unsupported operations remain in the existing retry/failure lifecycle and must not be promoted silently.

Production containers provision `ffmpeg`/`ffprobe` and readiness verifies both binaries are discoverable. Override `NFL_FIDOS_FFMPEG` and `NFL_FIDOS_FFPROBE` only with approved, pinned executable paths; a missing production binary is a deployment blocker.

The worker also supports bounded `transcode`, `segment`, and `thumbnail` jobs through `media_transform.py`. Output paths must be new and inside an approved root; absent `ffmpeg`, transform jobs fail explicitly for retry or operator remediation.

Run `python scripts/media_pipeline_smoke.py` for a temporary end-to-end rehearsal of authorized ingest, managed storage, `ffprobe`-style worker processing, persisted output evidence, and cross-organization isolation. The rehearsal does not use production media or credentials.

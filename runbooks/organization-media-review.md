# Organization media review

This package composes already-authorized film assets, bounded clips, playlists, observations, and film QA into a tenant-scoped review artifact.

1. Register media through the existing authorized asset path. Do not pass unverified files or provider credentials into the review package.
2. Create bounded clips and reviewable playlists using the existing film services.
3. Submit `POST /v1/media/organization-review` as an analyst or coach staff member.
4. Resolve any integrity, tenancy, reference, or QA correction issue. A package with failed QA is rejected.
5. A program owner may validate with `POST /v1/media/organization-review/approve` and a `DEC-*` or `APPROVAL-*` reference.

Approval records review completion only. It does not deploy external storage, run a media worker, activate a production workflow, or authorize stage advancement.

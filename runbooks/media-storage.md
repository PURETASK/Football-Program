# Managed media storage

Use `copy_authorized_media` to create an organization/asset-scoped managed copy. The source must be inside an explicitly approved source root, the destination must be inside the managed storage root, and existing destinations are never overwritten. The operation records a SHA-256 digest and returns a non-destructive retention marker. Retention cleanup requires a separate approved change; this primitive never deletes source or managed media.

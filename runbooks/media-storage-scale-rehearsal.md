# Managed media storage scale rehearsal

Run `python scripts/media_storage_scale_rehearsal.py` to create a temporary two-organization media corpus and exercise authorized copying into organization/asset namespaces.

The rehearsal checks SHA-256 integrity, tenant-specific destination paths, duplicate non-overwrite behavior, approved-source-root enforcement, and retention planning without deletion. It uses temporary files only and never contacts external storage or changes production state.

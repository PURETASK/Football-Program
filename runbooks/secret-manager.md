# Secret Manager Wiring

Production authentication secrets may be projected into a mounted file by an approved external secret manager. Configure the provider-neutral boundary with:

```powershell
$env:NFL_FIDOS_SECRET_PROVIDER = "approved_secret_manager_mount"
$env:NFL_FIDOS_SECRET_MANAGER_NAME = "nfl-fidos-auth"
$env:NFL_FIDOS_SECRET_VERSION = "version-ref"
$env:NFL_FIDOS_SECRET_MANAGER_FILE = "C:\secrets\nfl-fidos-auth"
python scripts/secret_source_preflight.py --environment production
```

The preflight reports only source metadata, mount readability, version, and secret length; it never prints the secret. Missing provider metadata, unreadable mounts, short values, or conflicting inline configuration fail closed. This contract does not contact a provider or grant production activation.

Run `python scripts/secret_manager_mount_rehearsal.py` to exercise the provider-neutral mount contract with a temporary synthetic secret. The rehearsal verifies production-length validation, value-redacted reporting, resolution, and missing-mount failure without contacting a secret provider.

# Monitoring Registration

The provider-neutral monitoring boundary validates the structured JSONL sink, alert contract, sink-parent writability, and deployment registration evidence without contacting or registering with an external monitoring vendor.

For a production preflight, configure:

```powershell
$env:NFL_FIDOS_MONITORING_BACKEND = "structured_jsonl"
$env:NFL_FIDOS_MONITORING_REGISTRATION_REF = "MONITORING-REG-OWNER-001"
$env:NFL_FIDOS_OBSERVABILITY_PATH = "C:\approved\observability\events.jsonl"
python scripts/monitoring_registration_preflight.py --environment production
```

The report remains non-activating and requires deployment-owner registration evidence for production. Backend credentials and vendor registration are intentionally external to this repository.

Run `python scripts/monitoring_registration_rehearsal.py` to exercise the validation and production metadata paths in a temporary workspace. The rehearsal checks alert coverage, sink writability, registration-reference requirements, and value-free output without contacting a monitoring vendor.

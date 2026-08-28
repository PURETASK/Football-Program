# Dashboard Smoke Check

Run this read-only check against a local or deployed NFL FIDOS HTTP service:

```powershell
$env:PYTHONPATH = "src"
python scripts/dashboard_smoke.py http://127.0.0.1:8000
```

The check verifies the dashboard shell, health endpoint, control-plane endpoint, and passing evaluation status. The smoke client allows up to 30 seconds for the cold full-evaluation endpoint. It does not mutate data, trigger scheduled work, or require external provider credentials. A passing result is supporting evidence only; it does not grant Stage 0 approval or authorize production deployment.

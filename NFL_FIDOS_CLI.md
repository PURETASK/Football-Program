# NFL FIDOS CLI

Run from the repository root with the bundled Python runtime and `PYTHONPATH=src`.

```text
python -m nfl_fidos.cli validate
python -m nfl_fidos.cli evals
python -m nfl_fidos.cli resolve shotgun
python -m nfl_fidos.cli compile path\to\play.json
```

All commands emit JSON. `compile` exits non-zero when the play compiler rejects a record; `evals` exits non-zero when any named evaluation family fails.

Run the non-destructive deployment-readiness check with:

```text
python scripts/readiness_check.py
```

It exits `0` only when runtime configuration, database integrity and migrations, evaluations, and the control plane are ready; otherwise it exits `1` with explicit blockers.

Validate the non-deploying release artifact gate with `PYTHONPATH=src python scripts/validate_release.py`. It verifies required packaging, CI, control, contract, and evaluation artifacts and reports owner approval as a release blocker.

Create a bounded scheduled-operations plan with `PYTHONPATH=src python scripts/scheduled_operations.py --organization-id ORG-... --actor ANALYST`. Planning is the default; add `--execute` only in an approved non-production environment.

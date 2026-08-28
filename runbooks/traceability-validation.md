# Traceability Evidence Validation

Run `PYTHONPATH=src python scripts/validate_traceability.py` to validate that the ledger covers exactly STAGE-0 through STAGE-25 and that every non-evaluation evidence reference exists in the repository. Evaluation-family references are checked by the evaluation suite.

This check proves evidence references are present; it does not convert foundation evidence into owner approval, production deployment, or real-organization validation.

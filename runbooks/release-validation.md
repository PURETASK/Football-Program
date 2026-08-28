# Release validation

Run `PYTHONPATH=src python scripts/validate_release.py` before any deployment request. The validator does not build, publish, or deploy an artifact. It checks required repository packaging and control files, runs the named evaluation suite, and reports the current stage/approval gate. A `blocked` result must be preserved as release evidence and remediated through the applicable human approval process.

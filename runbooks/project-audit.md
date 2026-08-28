# Project Audit Checkpoint

Run `PYTHONPATH=src python scripts/project_audit.py` to compose the current project checkpoint from the uploaded Markdown/DOCX conformance audit, traceability evidence validation, deterministic evaluation suite, and Stage 0 control manifest.

The command reports `foundation_verified` only when those checks pass. It always reports remaining stage work and sets `completion_claimed=false`; it cannot record owner approval, advance the stage, enable production, deploy services, or substitute for real organization/provider/pilot evidence.

# Organization Analytics Package Runbook

This workflow composes source-linked metric observations and reports for one organization and season. It preserves denominator context, uncertainty, lineage, and caveats; it does not contact providers, generalize sparse samples, or publish recommendations.

Analysts submit `POST /v1/analytics/organization-package`. Every observation source must be listed in the package source set, and every report must reference an observation in the same package. A program owner may validate the package with a DEC-* or APPROVAL-* reference. Production data adapters and empirical calibration remain separate deployment work.

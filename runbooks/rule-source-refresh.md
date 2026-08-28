# NFL Rule-Source Refresh Scheduling

Run `python scripts/schedule_rule_refresh.py` to produce a bounded freshness report for the official NFL rule-source registry. The scheduler validates the NFL jurisdiction and allowlisted HTTPS domain, identifies stale sources, and emits proposed review work.

The scheduler does not fetch content, rewrite the registry, promote a candidate, or bypass human jurisdiction review. A stale source must proceed through `plan_rule_source_refresh`, an owner decision record, and the existing non-promoting approval workflow.

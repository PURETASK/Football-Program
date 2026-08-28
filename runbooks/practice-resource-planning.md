# NFL FIDOS Practice Resource Planning

Practice plans may include an optional `resource_schedule` and `resource_availability` payload. The planner checks time windows, shared-resource overlaps, organization scope, facility availability, and staff availability before a plan can be persisted.

The planner is read-only with respect to external calendars: `external_calendar_mutation` is always `false`. A blocked resource plan remains visible as a draft response with conflict evidence and requires coach/staff resolution before publication.

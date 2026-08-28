# Practice Resource Integration

`POST /v1/practice/resources/preflight` accepts provider-supplied calendar or facility availability and passes it through the bounded practice-resource planner. The provider must be identified by an approved `SOURCE-*` or `PROVIDER-*` reference and must declare `mode: read_only`.

The endpoint is a validation boundary only. It does not fetch from a provider, reserve a facility, create a calendar event, or change external state. A successful result means the supplied availability can support the schedule; it still requires human review before a separately approved adapter could perform a reservation.

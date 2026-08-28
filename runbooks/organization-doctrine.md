# Organization Doctrine Package Runbook

This workflow compiles organization-scoped references to the controlled NFL offensive, defensive, and special-teams foundations. It does not infer private team doctrine and does not publish or activate a scheme.

Coaching staff submit `POST /v1/schemes/organization-doctrine` with an organization, team context, season, selected reference IDs, and authorized source references. The package remains `under_review` and every entry remains `review_required`. A program owner may submit `POST /v1/schemes/organization-doctrine/approve` with a DEC-* or APPROVAL-* reference. Approval only records validation evidence; production and stage advancement remain disabled.

Unknown reference IDs, missing source references, or empty packages are rejected. Real organization doctrine must be supplied and reviewed by the program owner before it can be used as team-specific context.

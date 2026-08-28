# Organization operating bundle

`organization_operating_bundle` composes the separate organization-scoped packages into a single readiness record. The API accepts either component payloads or explicit persisted component IDs; repository-backed resolution is tenant-scoped and missing records fail closed. It checks that the organization and season agree and that onboarding, terminology, doctrine, play corpus, player development, staff, drills, special teams, performance, media, scouting, analytics, and game-plan packages are in their required review states.

The output is an owner-review boundary only. Approval requires a `program_owner` and a `DEC-*` decision reference, and remains `approved_for_non_production`; it does not activate the organization, advance the stage, deploy services, call providers, or change external state.

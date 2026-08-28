"""NFL organization, season, roster, and staff context records."""

from __future__ import annotations

from typing import Any


PERSON_TYPES = {"player", "coach", "staff"}
STAFF_ROLES = {"head_coach", "coordinator", "position_coach", "analyst", "performance_staff", "medical_interface", "film_staff", "game_management"}


def build_organization_context(
    *,
    organization_id: str,
    name: str,
    season: str,
    people: list[dict[str, Any]],
    terminology_version: str,
    owner: str,
    source: dict[str, str],
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not organization_id.startswith("ORG-"):
        issues.append({"code": "ORG-ID", "message": "Organization id must start with ORG-", "path": "organization_id"})
    if not name or not season or not terminology_version or not owner:
        issues.append({"code": "ORG-METADATA", "message": "Name, season, terminology version, and owner are required", "path": "metadata"})
    if not source.get("kind") or not source.get("ref"):
        issues.append({"code": "ORG-SOURCE", "message": "Source kind and ref are required", "path": "source"})
    seen: set[str] = set()
    for index, person in enumerate(people):
        path = f"people[{index}]"
        if not person.get("id") or not person.get("name") or person.get("type") not in PERSON_TYPES:
            issues.append({"code": "ORG-PERSON", "message": "Person requires id, name, and player/coach/staff type", "path": path})
            continue
        if person["id"] in seen:
            issues.append({"code": "ORG-DUPLICATE-PERSON", "message": f"Duplicate person: {person['id']}", "path": path})
        seen.add(person["id"])
        if person["type"] in {"coach", "staff"} and person.get("staff_role") not in STAFF_ROLES:
            issues.append({"code": "ORG-STAFF-ROLE", "message": "Unknown staff role", "path": f"{path}.staff_role"})
        if person["type"] == "player" and not person.get("position"):
            issues.append({"code": "ORG-PLAYER-POSITION", "message": "Player position is required", "path": f"{path}.position"})
    return {
        "id": organization_id, "name": name, "league": "NFL", "season": season, "people": people,
        "terminology_version": terminology_version, "owner": owner, "source": source,
        "status": "rejected" if issues else "draft", "issues": issues,
    }


def resolve_person(context: dict[str, Any], person_id: str) -> dict[str, Any]:
    people = [person for person in context.get("people", []) if person.get("id") == person_id]
    if not people:
        return {"status": "unresolved", "person_id": person_id, "requires_review": True}
    if len(people) > 1:
        return {"status": "ambiguous", "person_id": person_id, "requires_review": True}
    return {"status": "resolved", "person": people[0], "organization_id": context.get("id"), "season": context.get("season"), "requires_review": False}

"""Validate source licensing/authorization evidence without fetching or registering a source."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


LICENSE_CLASSES = {"official_public", "licensed", "team_authorized"}
AUTHORIZATION_PREFIXES = ("LICENSE-", "DEC-", "APPROVAL-", "SOURCE-AUTH-")


def load_source_authorization(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_source_authorization(*, authorization: dict[str, Any], environment: str = "local") -> dict[str, Any]:
    issues: list[str] = []
    authorization_id = authorization.get("authorization_id")
    if not isinstance(authorization_id, str) or not authorization_id.startswith("AUTH-SOURCE-"):
        issues.append("authorization_id must start with AUTH-SOURCE-")
    organization_id = authorization.get("organization_id")
    if not isinstance(organization_id, str) or not organization_id.startswith("ORG-"):
        issues.append("organization_id must start with ORG-")
    source_id = authorization.get("source_id")
    if not isinstance(source_id, str) or not source_id.startswith("SOURCE-"):
        issues.append("source_id must start with SOURCE-")
    parsed = urlparse(str(authorization.get("uri", "")))
    if parsed.scheme != "https" or not parsed.hostname:
        issues.append("authorized source URI must be HTTPS with a hostname")
    license_class = authorization.get("license_class")
    if license_class not in LICENSE_CLASSES:
        issues.append("license_class must identify an approved source class")
    authorization_ref = authorization.get("authorization_ref")
    if not isinstance(authorization_ref, str) or not authorization_ref.startswith(AUTHORIZATION_PREFIXES):
        issues.append("authorization_ref must link to a license, decision, approval, or source authorization record")
    for field in ("approved_by", "approved_at"):
        if not isinstance(authorization.get(field), str) or not authorization[field].strip():
            issues.append(f"{field} is required")
    domains = authorization.get("allowed_domains")
    if not isinstance(domains, list) or not domains or not all(isinstance(domain, str) and domain.strip() for domain in domains):
        issues.append("allowed_domains must contain at least one non-empty domain")
    elif parsed.hostname and parsed.hostname.lower() not in {domain.lower() for domain in domains}:
        issues.append("source host must be covered by the authorized domain list")
    if authorization.get("external_fetch_allowed") is not True:
        issues.append("external_fetch_allowed must be explicitly true after authorization")
    if environment == "production" and license_class == "official_public" and not authorization_ref.startswith(("APPROVAL-", "SOURCE-AUTH-")):
        issues.append("production official sources require an explicit approval or source-authorization reference")
    return {
        "status": "authorized" if not issues else "blocked",
        "environment": environment,
        "authorization_id": authorization_id,
        "organization_id": organization_id,
        "source_id": source_id,
        "license_class": license_class,
        "authorized_domain_count": len(domains) if isinstance(domains, list) else 0,
        "external_fetch_allowed": authorization.get("external_fetch_allowed") is True,
        "network_fetch_performed": False,
        "external_state_changed": False,
        "issues": issues,
    }

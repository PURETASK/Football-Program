"""Dependency-free validation of the Dockerfile against the deployment contract."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .deployment_contract import validate_deployment_contract


def validate_deployment_infrastructure(*, dockerfile_path: str | Path, contract_path: str | Path) -> dict[str, Any]:
    dockerfile = Path(dockerfile_path)
    contract = Path(contract_path)
    issues: list[str] = []
    contract_result = validate_deployment_contract(path=contract)
    if contract_result.get("status") != "valid":
        issues.extend(f"deployment contract: {item}" for item in contract_result.get("issues", []))
    try:
        text = dockerfile.read_text(encoding="utf-8")
        data = json.loads(contract.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"status":"invalid", "dockerfile":str(dockerfile), "contract":str(contract), "issues":[str(exc)]}

    required_fragments = {
        "base_image":r"^FROM\s+python:3\.12-slim",
        "workdir":r"^WORKDIR\s+/app",
        "source_copy":r"^COPY\s+\.\s+\.",
        "package_install":"pip install --no-cache-dir .",
        "media_tool_install":"apt-get install -y --no-install-recommends ffmpeg",
        "volume":r"^VOLUME \[\"/var/lib/nfl-fidos\"\]$",
        "healthcheck":r"^HEALTHCHECK .*?/health",
        "command":r"^CMD \[\"nfl-fidos-server\"\]$",
    }
    for name, pattern in required_fragments.items():
        if not re.search(pattern, text, flags=re.MULTILINE):
            issues.append(f"Dockerfile missing required {name} instruction")
    service = next((item for item in data.get("services", []) if item.get("id") == "SERVICE-API"), {})
    port = service.get("port")
    if not re.search(rf"^EXPOSE\s+{re.escape(str(port))}\s*$", text, flags=re.MULTILINE):
        issues.append("Dockerfile EXPOSE does not match API service port")
    environment = data.get("environment_contract", {})
    for key in ("NFL_FIDOS_ENV", "NFL_FIDOS_HOST", "NFL_FIDOS_PORT", "NFL_FIDOS_DATABASE", "NFL_FIDOS_FFMPEG", "NFL_FIDOS_FFPROBE", "NFL_FIDOS_OBSERVABILITY_PATH"):
        if not re.search(rf"^ENV\s+{re.escape(key)}=", text, flags=re.MULTILINE):
            issues.append(f"Dockerfile must declare environment contract key {key}")
    if environment.get("NFL_FIDOS_ENV") == "production" and "NFL_FIDOS_AUTH_SECRET_FILE" not in text:
        issues.append("production image must declare the mounted authentication secret-file contract")
    return {"status":"valid" if not issues else "invalid", "dockerfile":str(dockerfile), "contract":str(contract), "issues":issues, "contract_status":contract_result.get("status"), "image_build_performed":False, "production_implementation_allowed":False}

"""Governed HTTPS source connectors with freshness and refresh evidence."""

from __future__ import annotations

import hashlib
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from urllib.parse import urlparse

from .research_protocol import register_research_source
from .tenant_repository import TenantRepository


Fetcher = Callable[[str, int], tuple[bytes, dict[str, str]]]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _default_fetcher(uri: str, max_bytes: int, *, allowed_domains: list[str] | None = None, timeout_seconds: int = 20) -> tuple[bytes, dict[str, str]]:
    parsed = urlparse(uri)
    allowed = {domain.lower() for domain in (allowed_domains or [])}
    if parsed.scheme != "https" or not parsed.hostname or parsed.hostname.lower() not in allowed:
        raise ValueError("source URI is outside the registered HTTPS domain allowlist")
    request = urllib.request.Request(uri, headers={"User-Agent": "NFL-FIDOS-authorized-source-connector/1.0"})
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        final_uri = response.geturl()
        final = urlparse(final_uri)
        if final.scheme != "https" or not final.hostname or final.hostname.lower() not in allowed:
            raise ValueError("source redirect left the registered HTTPS domain allowlist")
        content = response.read(max_bytes + 1)
        if len(content) > max_bytes:
            raise ValueError("source response exceeds configured maximum size")
        headers = {key.lower(): value for key, value in response.headers.items()}
        headers["x-nfl-fidos-final-uri"] = final_uri
        return content, headers


class SourceConnectorService:
    def __init__(self, repository: TenantRepository, *, fetcher: Fetcher | None = None):
        self.repository = repository
        self.fetcher = fetcher

    def register_source(self, *, source_id: str, tier: str, kind: str, uri: str, captured_at: str, effective_period: str, citation_location: str, owner: str, allowed_domains: list[str], freshness_days: int = 7, actor: str) -> dict[str, Any]:
        parsed = urlparse(uri)
        issues: list[str] = []
        if parsed.scheme != "https" or not parsed.hostname:
            issues.append("source connector must use an HTTPS URI")
        if parsed.hostname and parsed.hostname.lower() not in {domain.lower() for domain in allowed_domains}:
            issues.append("source host is not in the explicit authorized domain list")
        if not allowed_domains or freshness_days <= 0:
            issues.append("authorized domains and positive freshness_days are required")
        source = register_research_source(source_id=source_id, tier=tier, kind=kind, ref=uri, captured_at=captured_at, effective_period=effective_period, citation_location=citation_location, owner=owner, authorized=not issues)
        source.update({"organization_id": self.repository.organization_id, "uri": uri, "allowed_domains": allowed_domains, "freshness_days": freshness_days, "last_refresh": None})
        source["issues"] = list(source.get("issues", [])) + issues
        source["status"] = "registered" if not source["issues"] else "rejected"
        if source["status"] == "registered":
            return self.repository.put("knowledge_sources", source_id, source, actor=actor, reason="authorized_source_registered")
        return source

    def refresh_source(self, *, source_id: str, actor: str) -> dict[str, Any]:
        source = self.repository.get("knowledge_sources", source_id)
        if source is None:
            raise KeyError(f"Unknown source: {source_id}")
        if source.get("status") != "registered":
            raise ValueError("only registered sources may be refreshed")
        retrieved_at = _now()
        refresh_id = f"SOURCE-REFRESH-{source_id.removeprefix('SOURCE-')}-{retrieved_at.strftime('%Y%m%d%H%M%S%f')}"
        try:
            if self.fetcher is None and source.get("authorization_status") != "authorized":
                raise PermissionError("default external source refresh requires attached authorization evidence")
            if self.fetcher is None:
                content, headers = _default_fetcher(source["uri"], 10_000_000, allowed_domains=source.get("allowed_domains", []))
            else:
                content, headers = self.fetcher(source["uri"], 10_000_000)
            refresh = {"id":refresh_id, "organization_id":self.repository.organization_id, "source_id":source_id, "retrieved_at":retrieved_at.isoformat(), "sha256":hashlib.sha256(content).hexdigest(), "byte_count":len(content), "headers":headers, "status":"refreshed", "error":None}
            source.update({"last_refresh":retrieved_at.isoformat(), "last_sha256":refresh["sha256"], "status":"current", "updated_at":retrieved_at.isoformat()})
        except Exception as exc:
            refresh = {"id":refresh_id, "organization_id":self.repository.organization_id, "source_id":source_id, "retrieved_at":retrieved_at.isoformat(), "sha256":None, "byte_count":0, "headers":{}, "status":"failed", "error":str(exc)}
        self.repository.put("source_refreshes", refresh_id, refresh, actor=actor, reason="source_refresh_recorded")
        self.repository.put("knowledge_sources", source_id, source, actor=actor, reason="source_refresh_state_updated")
        return refresh

    def is_stale(self, source: dict[str, Any], *, now: datetime | None = None) -> bool:
        if not source.get("last_refresh"):
            return True
        refreshed = datetime.fromisoformat(source["last_refresh"])
        return (now or _now()) - refreshed > timedelta(days=source.get("freshness_days", 1))

    def list_sources(self) -> list[dict[str, Any]]:
        return [{**source, "stale": self.is_stale(source)} for source in self.repository.list("knowledge_sources")]

    def refresh_all(self, *, actor: str, stale_only: bool = True, max_sources: int = 100) -> dict[str, Any]:
        if max_sources <= 0:
            raise ValueError("max_sources must be positive")
        started_at = _now()
        sources = [source for source in self.list_sources() if source.get("status") in {"registered", "current"}]
        if stale_only:
            sources = [source for source in sources if source.get("stale")]
        selected = sources[:max_sources]
        results: list[dict[str, Any]] = []
        for source in selected:
            try:
                results.append(self.refresh_source(source_id=source["id"], actor=actor))
            except (KeyError, ValueError) as exc:
                results.append({"source_id":source.get("id"), "status":"failed", "error":str(exc)})
        failed = sum(1 for result in results if result.get("status") == "failed")
        return {"id":f"SOURCE-REFRESH-BATCH-{started_at.strftime('%Y%m%d%H%M%S%f')}", "organization_id":self.repository.organization_id, "started_at":started_at.isoformat(), "finished_at":_now().isoformat(), "stale_only":stale_only, "max_sources":max_sources, "selected_count":len(selected), "refreshed_count":len(results) - failed, "failed_count":failed, "status":"partial_failure" if failed else "completed", "results":results, "human_review_required":bool(failed)}

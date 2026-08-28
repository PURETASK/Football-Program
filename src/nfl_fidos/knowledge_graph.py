"""Versioned, provenance-bearing NFL knowledge graph primitives."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


class KnowledgeGraph:
    def __init__(self, *, organization_id: str):
        if not organization_id:
            raise ValueError("organization_id is required")
        self.organization_id = organization_id
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: dict[str, dict[str, Any]] = {}

    def add_node(self, *, node_id: str, label: str, node_type: str, source_refs: list[str], context: dict[str, Any], classification: str = "fact", confidence: str = "moderate", state: str = "proposed") -> dict[str, Any]:
        issues: list[str] = []
        if not node_id or not label or not node_type or not source_refs or not context:
            issues.append("node identity, label, type, source refs, and context are required")
        if classification not in {"fact","rule","team_rule","observed_tendency","coaching_preference","contextual_principle","hypothesis"}:
            issues.append("invalid claim classification")
        if confidence not in {"low","moderate","high"}:
            issues.append("invalid confidence")
        if state not in {"proposed","current","historical","superseded","unresolved"}:
            issues.append("invalid node state")
        record = {"id":node_id, "label":label, "node_type":node_type, "organization_id":self.organization_id, "source_refs":source_refs, "context":context, "classification":classification, "confidence":confidence, "state":state, "canonical_allowed":not issues and classification != "hypothesis" and state in {"current","historical"}, "status":"invalid" if issues else "proposed", "issues":issues}
        if not issues:
            self.nodes[node_id] = record
        return deepcopy(record)

    def add_edge(self, *, edge_id: str, from_id: str, to_id: str, relation: str, source_refs: list[str], context: dict[str, Any], confidence: str = "moderate") -> dict[str, Any]:
        issues: list[str] = []
        if not edge_id or not from_id or not to_id or not relation or not source_refs or not context:
            issues.append("edge identity, endpoints, relation, source refs, and context are required")
        if from_id not in self.nodes or to_id not in self.nodes:
            issues.append("edge endpoints must already exist")
        if confidence not in {"low","moderate","high"}:
            issues.append("invalid confidence")
        canonical_allowed = not issues and self.nodes.get(from_id, {}).get("canonical_allowed") and self.nodes.get(to_id, {}).get("canonical_allowed") and confidence != "low"
        record = {"id":edge_id, "from_id":from_id, "to_id":to_id, "relation":relation, "organization_id":self.organization_id, "source_refs":source_refs, "context":context, "confidence":confidence, "canonical_allowed":bool(canonical_allowed), "status":"needs_review" if issues or not canonical_allowed else "proposed", "human_review_required":not canonical_allowed, "issues":issues}
        if not issues:
            self.edges[edge_id] = record
        return deepcopy(record)

    def review_edge(self, *, edge_id: str, reviewer: str, decision: str, reason: str) -> dict[str, Any]:
        if edge_id not in self.edges or not reviewer or decision not in {"approve","reject"} or not reason:
            raise ValueError("edge, reviewer, decision, and reason are required")
        edge = self.edges[edge_id]
        edge.update({"reviewer":reviewer, "review_reason":reason, "status":"current" if decision == "approve" else "rejected", "canonical_allowed":decision == "approve", "human_review_required":False})
        return deepcopy(edge)

    def neighbors(self, node_id: str, *, relation: str | None = None) -> list[dict[str, Any]]:
        if node_id not in self.nodes:
            return []
        connected: list[dict[str, Any]] = []
        for edge in self.edges.values():
            if relation and edge.get("relation") != relation:
                continue
            if edge.get("from_id") == node_id:
                connected.append({"direction":"out", "edge":deepcopy(edge), "node":deepcopy(self.nodes[edge["to_id"]])})
            elif edge.get("to_id") == node_id:
                connected.append({"direction":"in", "edge":deepcopy(edge), "node":deepcopy(self.nodes[edge["from_id"]])})
        return connected

    def snapshot(self) -> dict[str, Any]:
        return {"organization_id":self.organization_id, "nodes":deepcopy(list(self.nodes.values())), "edges":deepcopy(list(self.edges.values()))}

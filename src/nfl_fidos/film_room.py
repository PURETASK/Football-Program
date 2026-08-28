"""Organization-scoped film-room search, annotation sessions, and quiz mode."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


class FilmRoomIndex:
    def __init__(self, *, organization_id: str):
        if not organization_id:
            raise ValueError("organization_id is required")
        self.organization_id = organization_id
        self._records: dict[str, dict[str, Any]] = {}

    def add(self, record: dict[str, Any]) -> None:
        if record.get("organization_id") != self.organization_id:
            raise PermissionError("film record is outside organization scope")
        if not record.get("id"):
            raise ValueError("film record id is required")
        self._records[record["id"]] = deepcopy(record)

    def search(self, *, query: str = "", team: str | None = None, opponent: str | None = None, domain: str | None = None, label: str | None = None, confidence: str | None = None) -> list[dict[str, Any]]:
        normalized = query.strip().lower()
        results: list[dict[str, Any]] = []
        for record in self._records.values():
            context = record.get("context", {})
            if team and context.get("team") != team:
                continue
            if opponent and context.get("opponent") != opponent:
                continue
            if domain and record.get("domain") != domain:
                continue
            if label and record.get("label") != label:
                continue
            if confidence and record.get("confidence") != confidence:
                continue
            searchable = " ".join(str(record.get(field, "")) for field in ("id", "label", "domain", "evidence")) + " " + str(context)
            if normalized and normalized not in searchable.lower():
                continue
            results.append(deepcopy(record))
        return sorted(results, key=lambda record: record.get("id", ""))


def build_annotation_session(*, session_id: str, clip_id: str, organization_id: str, annotator: str, allowed_domains: list[str], source_refs: list[str]) -> dict[str, Any]:
    issues: list[str] = []
    if not session_id.startswith("ANNOTATION-") or not clip_id.startswith("CLIP-") or not organization_id or not annotator or not allowed_domains or not source_refs:
        issues.append("session, clip, organization, annotator, domains, and source refs are required")
    return {"id":session_id, "clip_id":clip_id, "organization_id":organization_id, "annotator":annotator, "allowed_domains":allowed_domains, "source_refs":source_refs, "annotations":[], "status":"open" if not issues else "invalid", "issues":issues, "correction_required":False}


def append_annotation(*, session: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
    output = deepcopy(session)
    issues = list(output.get("issues", []))
    if output.get("status") != "open":
        issues.append("annotation session is not open")
    if observation.get("clip_id") != output.get("clip_id"):
        issues.append("observation clip does not match session clip")
    if observation.get("organization_id") != output.get("organization_id"):
        issues.append("observation organization does not match session organization")
    if observation.get("domain") not in output.get("allowed_domains", []):
        issues.append("observation domain is not allowed in this session")
    output.setdefault("annotations", []).append(deepcopy(observation))
    output["issues"] = issues
    output["correction_required"] = any(item.get("status") in {"needs_review", "invalid"} or item.get("confidence") == "low" for item in output["annotations"])
    return output


def build_film_quiz(*, quiz_id: str, title: str, organization_id: str, role: str, clip_ids: list[str], questions: list[dict[str, Any]], owner: str) -> dict[str, Any]:
    issues: list[str] = []
    if not quiz_id.startswith("QUIZ-") or not title or not organization_id or not role or not clip_ids or not questions or not owner:
        issues.append("quiz identity, organization, role, clips, questions, and owner are required")
    if any(not clip_id.startswith("CLIP-") for clip_id in clip_ids):
        issues.append("quiz clip references must be CLIP-* ids")
    for index, question in enumerate(questions):
        if not question.get("id") or not question.get("prompt") or "expected_answer" not in question or not question.get("evidence_refs"):
            issues.append(f"question {index} requires id, prompt, expected answer, and evidence refs")
    return {"id":quiz_id, "title":title, "organization_id":organization_id, "role":role, "clip_ids":clip_ids, "questions":questions, "owner":owner, "status":"draft" if not issues else "invalid", "issues":issues, "human_review_required":True}


def submit_film_quiz(*, attempt_id: str, quiz: dict[str, Any], participant: str, answers: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    if not attempt_id.startswith("QUIZ-ATTEMPT-") or not participant:
        issues.append("attempt id and participant are required")
    if quiz.get("status") not in {"draft", "published"}:
        issues.append("quiz must be valid before submission")
    graded = []
    correct = 0
    for question in quiz.get("questions", []):
        answer = answers.get(question.get("id"))
        is_correct = answer == question.get("expected_answer")
        correct += int(is_correct)
        graded.append({"question_id":question.get("id"), "answer":answer, "correct":is_correct, "evidence_refs":question.get("evidence_refs", [])})
    total = len(quiz.get("questions", []))
    return {"id":attempt_id, "quiz_id":quiz.get("id"), "organization_id":quiz.get("organization_id"), "participant":participant, "graded_answers":graded, "score":correct / total if total else None, "status":"invalid" if issues else "under_review", "issues":issues, "human_review_required":True}

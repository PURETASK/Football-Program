"""Repository-backed, organization-scoped film-room service."""

from __future__ import annotations

import base64
import binascii
from datetime import datetime, timezone
from typing import Any

from .film_room import FilmRoomIndex, append_annotation, build_annotation_session, build_film_quiz, submit_film_quiz
from .film_intelligence import build_film_playlist, normalize_film_links
from .tenant_repository import TenantRepository
from .film_search import FilmSearchIndex


class FilmRoomService:
    def __init__(self, repository: TenantRepository):
        self.repository = repository
        connection = getattr(repository.repository, "connection", None)
        self.search_index = FilmSearchIndex(connection) if connection is not None else None
        if self.search_index and self.search_index.available:
            for record in repository.list("film_observations"):
                self.search_index.upsert(record)

    def save_observation(self, observation: dict[str, Any], *, actor: str) -> dict[str, Any]:
        if observation.get("organization_id") != self.repository.organization_id:
            raise PermissionError("observation organization does not match service scope")
        scoped_observation = dict(observation)
        linked_record_refs, link_issues = normalize_film_links(scoped_observation.get("linked_record_refs"))
        if link_issues:
            raise ValueError("; ".join(issue["message"] for issue in link_issues))
        scoped_observation["linked_record_refs"] = linked_record_refs
        saved = self.repository.put("film_observations", scoped_observation["id"], scoped_observation, actor=actor, reason="film_observation_saved")
        if self.search_index:
            self.search_index.upsert(saved)
        return saved

    def search(self, **filters: Any) -> list[dict[str, Any]]:
        if self.search_index and self.search_index.available:
            ids = self.search_index.search(organization_id=self.repository.organization_id, **filters)
            records = [self.repository.get("film_observations", record_id) for record_id in ids]
            return [record for record in records if record is not None]
        index = FilmRoomIndex(organization_id=self.repository.organization_id)
        for observation in self.repository.list("film_observations"):
            index.add(observation)
        return index.search(**filters)

    def create_quiz(self, *, quiz_id: str, title: str, role: str, clip_ids: list[str], questions: list[dict[str, Any]], owner: str, actor: str) -> dict[str, Any]:
        quiz = build_film_quiz(quiz_id=quiz_id, title=title, organization_id=self.repository.organization_id, role=role, clip_ids=clip_ids, questions=questions, owner=owner)
        return self.repository.put("film_quizzes", quiz_id, quiz, actor=actor, reason="film_quiz_created")

    def submit_quiz(self, *, attempt_id: str, quiz_id: str, participant: str, answers: dict[str, Any], actor: str) -> dict[str, Any]:
        quiz = self.repository.get("film_quizzes", quiz_id)
        if quiz is None:
            raise KeyError(f"Unknown film quiz: {quiz_id}")
        attempt = submit_film_quiz(attempt_id=attempt_id, quiz=quiz, participant=participant, answers=answers)
        return self.repository.put("film_quiz_attempts", attempt_id, attempt, actor=actor, reason="film_quiz_attempt_recorded")

    def create_playlist(self, *, playlist_id: str, name: str, purpose: str, clip_ids: list[str], filters: dict[str, Any], owner: str, access_roles: list[str], actor: str) -> dict[str, Any]:
        clips = {clip.get("id") for clip in self.repository.list("film_clips")}
        missing = [clip_id for clip_id in clip_ids if clip_id not in clips]
        if missing:
            raise KeyError(f"Unknown organization-scoped clips: {', '.join(missing)}")
        playlist = build_film_playlist(playlist_id=playlist_id, name=name, purpose=purpose, clip_ids=clip_ids, filters=filters, owner=owner, access_roles=access_roles)
        if playlist["status"] != "draft":
            return playlist
        playlist["organization_id"] = self.repository.organization_id
        return self.repository.put("film_playlists", playlist_id, playlist, actor=actor, reason="film_playlist_created")

    def list_playlists(self, *, role: str) -> list[dict[str, Any]]:
        if role == "program_owner":
            return self.repository.list("film_playlists")
        return [playlist for playlist in self.repository.list("film_playlists") if role in playlist.get("access_roles", [])]

    def create_annotation_session(self, *, session_id: str, clip_id: str, annotator: str, allowed_domains: list[str], source_refs: list[str], actor: str) -> dict[str, Any]:
        session = build_annotation_session(session_id=session_id, clip_id=clip_id, organization_id=self.repository.organization_id, annotator=annotator, allowed_domains=allowed_domains, source_refs=source_refs)
        if session["status"] != "open":
            return session
        return self.repository.put("film_annotation_sessions", session_id, session, actor=actor, reason="film_annotation_session_created")

    def append_session_annotation(self, *, session_id: str, observation: dict[str, Any], actor: str) -> dict[str, Any]:
        session = self.repository.get("film_annotation_sessions", session_id)
        if session is None:
            raise KeyError(f"Unknown annotation session: {session_id}")
        scoped_observation = dict(observation)
        scoped_observation["organization_id"] = self.repository.organization_id
        linked_record_refs, link_issues = normalize_film_links(scoped_observation.get("linked_record_refs"))
        if link_issues:
            raise ValueError("; ".join(issue["message"] for issue in link_issues))
        scoped_observation["linked_record_refs"] = linked_record_refs
        updated = append_annotation(session=session, observation=scoped_observation)
        return self.repository.put("film_annotation_sessions", session_id, updated, actor=actor, reason="film_annotation_appended")

    def create_voice_note(
        self,
        *,
        note_id: str,
        clip_id: str,
        frame_seconds: float,
        mime_type: str,
        audio_data: str,
        transcript: str,
        access_roles: list[str],
        author: str,
        actor: str,
    ) -> dict[str, Any]:
        """Persist a bounded, clip-linked voice note for local media workflows.

        The payload limit is intentional. Production deployments should replace
        the inline data URL with managed encrypted media storage; the record
        still preserves the same clip/frame/provenance contract.
        """
        if not note_id.startswith("VOICE-NOTE-"):
            raise ValueError("note_id must start with VOICE-NOTE-")
        if not clip_id or frame_seconds < 0 or not transcript.strip():
            raise ValueError("clip_id, non-negative frame_seconds, and transcript are required")
        if not mime_type.startswith("audio/"):
            raise ValueError("mime_type must be an audio media type")
        if not audio_data.startswith("data:") or ";base64," not in audio_data:
            raise ValueError("audio_data must be a base64 data URL")
        try:
            encoded = audio_data.split(";base64,", 1)[1]
            decoded = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ValueError("audio_data is not valid base64") from exc
        if not decoded:
            raise ValueError("audio_data cannot be empty")
        if len(decoded) > 262_144:
            raise ValueError("voice note payload exceeds the 256 KiB limit")
        clip = self.repository.get("film_clips", clip_id)
        if clip is None:
            raise KeyError(f"Unknown organization-scoped clip: {clip_id}")
        note = {
            "id": note_id,
            "organization_id": self.repository.organization_id,
            "clip_id": clip_id,
            "asset_id": clip.get("asset_id"),
            "frame_seconds": round(float(frame_seconds), 3),
            "mime_type": mime_type,
            "audio_data": audio_data,
            "byte_size": len(decoded),
            "transcript": transcript.strip(),
            "access_roles": access_roles or ["program_owner", "coach_staff", "analyst"],
            "created_by": author,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "storage_boundary": "inline_local_bounded_payload; replace with encrypted managed media storage before production",
            "status": "ready_for_review",
        }
        return self.repository.put("film_voice_notes", note_id, note, actor=actor, reason="film_voice_note_created")

    def list_voice_notes(self, *, role: str) -> list[dict[str, Any]]:
        notes = self.repository.list("film_voice_notes")
        if role == "program_owner":
            return notes
        return [note for note in notes if role in note.get("access_roles", [])]

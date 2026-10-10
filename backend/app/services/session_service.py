"""In-memory session storage with expiration.

Sessions are lost when the process restarts. Run a single worker process so all requests
share one store.
"""

from __future__ import annotations

import asyncio
import secrets
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from app.errors import SessionNotFoundError


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class StoredQuestion:
    id: str
    concept_id: str
    question: str
    options: list[str]  # exactly 4, in display order A-D
    correct_index: int
    explanation: str


@dataclass
class Session:
    id: str
    document_name: str
    created_at: datetime
    expires_at: datetime
    concepts: list[dict[str, Any]]  # validated concept dicts (id, name, description, difficulty, prerequisites, source_type)
    # Bounded excerpt of the document, kept only until the quiz has been generated.
    quiz_context: str | None = None
    questions: list[StoredQuestion] | None = None
    results: dict[str, Any] | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)


class SessionStore:
    def __init__(self, ttl_minutes: int, max_sessions: int):
        self._ttl = timedelta(minutes=ttl_minutes)
        self._max = max_sessions
        self._sessions: dict[str, Session] = {}
        self._guard = threading.Lock()

    def create(self, document_name: str, concepts: list[dict[str, Any]], quiz_context: str | None) -> Session:
        now = utcnow()
        session = Session(
            id=secrets.token_urlsafe(24),
            document_name=document_name,
            created_at=now,
            expires_at=now + self._ttl,
            concepts=concepts,
            quiz_context=quiz_context,
        )
        with self._guard:
            self._purge_expired_locked(now)
            while len(self._sessions) >= self._max:
                oldest = min(self._sessions.values(), key=lambda s: s.created_at)
                del self._sessions[oldest.id]
            self._sessions[session.id] = session
        return session

    def get(self, session_id: str) -> Session:
        now = utcnow()
        with self._guard:
            session = self._sessions.get(session_id)
            if session is None:
                raise SessionNotFoundError()
            if session.expires_at <= now:
                del self._sessions[session_id]
                raise SessionNotFoundError()
            return session

    def count(self) -> int:
        with self._guard:
            self._purge_expired_locked(utcnow())
            return len(self._sessions)

    def clear(self) -> None:
        with self._guard:
            self._sessions.clear()

    def _purge_expired_locked(self, now: datetime) -> None:
        for sid in [sid for sid, s in self._sessions.items() if s.expires_at <= now]:
            del self._sessions[sid]

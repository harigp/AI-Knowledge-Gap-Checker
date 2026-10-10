"""
store.py: session persistence for ConceptGraph AI.

Routes never touch SQL. They call a SessionStore, and one environment
variable decides which implementation they get:

    STORE_BACKEND=sqlite   (default)  data survives restarts, if the disk does
    STORE_BACKEND=memory              the original in-memory MVP; flip to this if
                                      the database ever causes trouble
    DB_PATH=conceptgraph.db           where the SQLite file lives

Usage:
    from store import get_store
    store = get_store()
    sid = store.create_session("notes.pdf", file_hash)

Rules:
- save_concepts / save_quiz / save_attempt also advance the session status
  (graph_ready / quiz_ready / completed).
- Mutators on a missing session raise SessionNotFound (map to HTTP 404).
- Feed save_concepts a graph that already passed validate_graph.
- Both implementations return COPIES, so mutating a result never changes stored data.
"""

import json
import os
import sqlite3
import threading
import uuid
from abc import ABC, abstractmethod
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from functools import lru_cache

from models import (
    Concept,
    LearningSession,
    QuizQuestion,
    QuizQuestionPrivate,
    ResultsResponse,
    SessionStatus,
)

CACHEABLE_STATUSES = ("quiz_ready", "completed")


class SessionNotFound(KeyError):
    """Raised when an operation targets a session id that doesn't exist."""


def _new_id() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    # Fixed format so ISO strings sort correctly as plain text
    return dt.isoformat(timespec="microseconds")


def _check_unique(ids: list[str], what: str) -> None:
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate {what} ids; validate before saving")


# ======================================================================
# Interface
# ======================================================================

class SessionStore(ABC):
    # ---- implemented by each backend ----

    @abstractmethod
    def create_session(self, document_name: str, file_hash: str | None = None) -> str: ...

    @abstractmethod
    def get_session(self, session_id: str) -> LearningSession | None:
        """Full session (concepts, private questions, latest results) or None."""

    @abstractmethod
    def set_status(self, session_id: str, status: SessionStatus) -> None: ...

    @abstractmethod
    def save_concepts(self, session_id: str, concepts: list[Concept]) -> None:
        """Replace the session's concepts and prerequisite edges. Status -> graph_ready."""

    @abstractmethod
    def save_quiz(self, session_id: str, questions: list[QuizQuestionPrivate]) -> None:
        """Replace the session's quiz (with answer keys). Status -> quiz_ready."""

    @abstractmethod
    def save_attempt(
        self, session_id: str, answers: dict[str, int], results: ResultsResponse
    ) -> int:
        """Store a submission. Returns its 1-based attempt number. Status -> completed."""

    @abstractmethod
    def get_attempts(self, session_id: str) -> list[ResultsResponse]:
        """Every attempt's results, oldest first (for before/after comparisons)."""

    @abstractmethod
    def find_by_file_hash(self, file_hash: str) -> LearningSession | None:
        """Newest session for this file that already has a graph AND quiz (demo cache)."""

    @abstractmethod
    def pin_session(self, session_id: str) -> None:
        """Exempt a session from delete_expired (e.g. the cached demo PDF)."""

    @abstractmethod
    def delete_expired(self, max_age_seconds: float) -> int:
        """Delete unpinned sessions older than max_age_seconds. Returns how many."""

    # ---- shared, built on get_session ----

    def _require(self, session_id: str) -> LearningSession:
        session = self.get_session(session_id)
        if session is None:
            raise SessionNotFound(session_id)
        return session

    def get_concepts(self, session_id: str) -> list[Concept]:
        return self._require(session_id).concepts

    def get_quiz(
        self, session_id: str, include_answers: bool = False
    ) -> list[QuizQuestion] | list[QuizQuestionPrivate]:
        """Questions without answer keys by default. [] if no quiz has been saved yet."""
        questions = self._require(session_id).questions
        return questions if include_answers else [q.to_public() for q in questions]

    def get_results(self, session_id: str) -> ResultsResponse | None:
        """Latest results, or None if the quiz hasn't been submitted."""
        return self._require(session_id).results

    def clone_session(self, source_id: str) -> str:
        """New session with the source's concepts and quiz but no results.

        Use after find_by_file_hash so every student attempt gets its own session.
        """
        src = self._require(source_id)
        new_id = self.create_session(src.document_name, src.file_hash)
        if src.concepts:
            self.save_concepts(new_id, src.concepts)
        if src.questions:
            self.save_quiz(new_id, src.questions)
        return new_id


# ======================================================================
# In-memory backend
# ======================================================================

class InMemoryStore(SessionStore):
    def __init__(self):
        self._lock = threading.RLock()
        self._sessions: dict[str, LearningSession] = {}
        self._attempts: dict[str, list[tuple[dict[str, int], ResultsResponse]]] = {}
        self._pinned: set[str] = set()

    def _live(self, session_id: str) -> LearningSession:
        """The stored object itself (callers must hold the lock)."""
        try:
            return self._sessions[session_id]
        except KeyError:
            raise SessionNotFound(session_id) from None

    def create_session(self, document_name, file_hash=None):
        sid = _new_id()
        with self._lock:
            self._sessions[sid] = LearningSession(
                id=sid, document_name=document_name, file_hash=file_hash
            )
            self._attempts[sid] = []
        return sid

    def get_session(self, session_id):
        with self._lock:
            s = self._sessions.get(session_id)
            return s.model_copy(deep=True) if s else None

    def set_status(self, session_id, status):
        with self._lock:
            self._live(session_id).status = status

    def save_concepts(self, session_id, concepts):
        _check_unique([c.id for c in concepts], "concept")
        with self._lock:
            s = self._live(session_id)
            s.concepts = [c.model_copy(deep=True) for c in concepts]
            s.status = "graph_ready"

    def save_quiz(self, session_id, questions):
        _check_unique([q.id for q in questions], "question")
        with self._lock:
            s = self._live(session_id)
            s.questions = [q.model_copy(deep=True) for q in questions]
            s.status = "quiz_ready"

    def save_attempt(self, session_id, answers, results):
        with self._lock:
            s = self._live(session_id)
            self._attempts[session_id].append((dict(answers), results.model_copy(deep=True)))
            s.results = results.model_copy(deep=True)
            s.status = "completed"
            return len(self._attempts[session_id])

    def get_attempts(self, session_id):
        with self._lock:
            self._live(session_id)
            return [r.model_copy(deep=True) for _, r in self._attempts[session_id]]

    def find_by_file_hash(self, file_hash):
        with self._lock:
            matches = [
                s for s in self._sessions.values()
                if s.file_hash == file_hash and s.status in CACHEABLE_STATUSES
            ]
            if not matches:
                return None
            return max(matches, key=lambda s: s.created_at).model_copy(deep=True)

    def pin_session(self, session_id):
        with self._lock:
            self._live(session_id)
            self._pinned.add(session_id)

    def delete_expired(self, max_age_seconds):
        cutoff = _now() - timedelta(seconds=max_age_seconds)
        with self._lock:
            expired = [
                sid for sid, s in self._sessions.items()
                if s.created_at < cutoff and sid not in self._pinned
            ]
            for sid in expired:
                del self._sessions[sid]
                self._attempts.pop(sid, None)
            return len(expired)


# ======================================================================
# SQLite backend
# ======================================================================

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id            TEXT PRIMARY KEY,
    document_name TEXT NOT NULL,
    file_hash     TEXT,
    status        TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    pinned        INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_sessions_hash ON sessions(file_hash);

CREATE TABLE IF NOT EXISTS concepts (
    session_id  TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    id          TEXT NOT NULL,
    position    INTEGER NOT NULL,
    name        TEXT NOT NULL,
    description TEXT NOT NULL,
    difficulty  TEXT NOT NULL,
    source_type TEXT NOT NULL,
    PRIMARY KEY (session_id, id)
);

-- the graph's edge table: prerequisite_id -> concept_id
CREATE TABLE IF NOT EXISTS prerequisites (
    session_id      TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    concept_id      TEXT NOT NULL,
    prerequisite_id TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_prereq_session ON prerequisites(session_id);

CREATE TABLE IF NOT EXISTS questions (
    session_id    TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    id            TEXT NOT NULL,
    position      INTEGER NOT NULL,
    concept_id    TEXT NOT NULL,
    question      TEXT NOT NULL,
    options       TEXT NOT NULL,   -- JSON array of 4 strings
    explanation   TEXT NOT NULL,
    correct_index INTEGER NOT NULL,
    PRIMARY KEY (session_id, id)
);

CREATE TABLE IF NOT EXISTS attempts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    answers    TEXT NOT NULL,      -- JSON {question_id: chosen_index}
    results    TEXT NOT NULL,      -- JSON ResultsResponse (includes per-concept scores)
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_attempts_session ON attempts(session_id);
"""


class SqliteStore(SessionStore):
    def __init__(self, path: str = "conceptgraph.db"):
        self.path = path
        self.init_db()

    @contextmanager
    def _conn(self):
        # One short-lived connection per operation: safe with FastAPI's threadpool.
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")  # must be set on every connection
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_db(self) -> None:
        with self._conn() as conn:
            conn.executescript(SCHEMA)

    @staticmethod
    def _require_row(conn, session_id: str) -> None:
        if conn.execute("SELECT 1 FROM sessions WHERE id = ?", (session_id,)).fetchone() is None:
            raise SessionNotFound(session_id)

    # ---- writes ----

    def create_session(self, document_name, file_hash=None):
        sid = _new_id()
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO sessions (id, document_name, file_hash, status, created_at) "
                "VALUES (?, ?, ?, 'created', ?)",
                (sid, document_name, file_hash, _iso(_now())),
            )
        return sid

    def set_status(self, session_id, status):
        with self._conn() as conn:
            cur = conn.execute("UPDATE sessions SET status = ? WHERE id = ?", (status, session_id))
            if cur.rowcount == 0:
                raise SessionNotFound(session_id)

    def save_concepts(self, session_id, concepts):
        _check_unique([c.id for c in concepts], "concept")
        with self._conn() as conn:
            self._require_row(conn, session_id)
            conn.execute("DELETE FROM concepts WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM prerequisites WHERE session_id = ?", (session_id,))
            conn.executemany(
                "INSERT INTO concepts (session_id, id, position, name, description, difficulty, source_type) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    (session_id, c.id, i, c.name, c.description, c.difficulty, c.source_type)
                    for i, c in enumerate(concepts)
                ],
            )
            conn.executemany(
                "INSERT INTO prerequisites (session_id, concept_id, prerequisite_id) VALUES (?, ?, ?)",
                [(session_id, c.id, p) for c in concepts for p in c.prerequisite_ids],
            )
            conn.execute("UPDATE sessions SET status = 'graph_ready' WHERE id = ?", (session_id,))

    def save_quiz(self, session_id, questions):
        _check_unique([q.id for q in questions], "question")
        with self._conn() as conn:
            self._require_row(conn, session_id)
            conn.execute("DELETE FROM questions WHERE session_id = ?", (session_id,))
            conn.executemany(
                "INSERT INTO questions "
                "(session_id, id, position, concept_id, question, options, explanation, correct_index) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                [
                    (session_id, q.id, i, q.concept_id, q.question,
                     json.dumps(q.options), q.explanation, q.correct_index)
                    for i, q in enumerate(questions)
                ],
            )
            conn.execute("UPDATE sessions SET status = 'quiz_ready' WHERE id = ?", (session_id,))

    def save_attempt(self, session_id, answers, results):
        with self._conn() as conn:
            self._require_row(conn, session_id)
            conn.execute(
                "INSERT INTO attempts (session_id, answers, results, created_at) VALUES (?, ?, ?, ?)",
                (session_id, json.dumps(answers), results.model_dump_json(), _iso(_now())),
            )
            conn.execute("UPDATE sessions SET status = 'completed' WHERE id = ?", (session_id,))
            return conn.execute(
                "SELECT COUNT(*) FROM attempts WHERE session_id = ?", (session_id,)
            ).fetchone()[0]

    def pin_session(self, session_id):
        with self._conn() as conn:
            cur = conn.execute("UPDATE sessions SET pinned = 1 WHERE id = ?", (session_id,))
            if cur.rowcount == 0:
                raise SessionNotFound(session_id)

    def delete_expired(self, max_age_seconds):
        cutoff = _iso(_now() - timedelta(seconds=max_age_seconds))
        with self._conn() as conn:
            # ON DELETE CASCADE removes the children
            cur = conn.execute(
                "DELETE FROM sessions WHERE created_at < ? AND pinned = 0", (cutoff,)
            )
            return cur.rowcount

    # ---- reads ----

    def get_session(self, session_id):
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
            if row is None:
                return None

            prereqs: dict[str, list[str]] = {}
            for r in conn.execute(
                "SELECT concept_id, prerequisite_id FROM prerequisites "
                "WHERE session_id = ? ORDER BY rowid",
                (session_id,),
            ):
                prereqs.setdefault(r["concept_id"], []).append(r["prerequisite_id"])

            concepts = [
                Concept(
                    id=r["id"],
                    name=r["name"],
                    description=r["description"],
                    difficulty=r["difficulty"],
                    source_type=r["source_type"],
                    prerequisite_ids=prereqs.get(r["id"], []),
                )
                for r in conn.execute(
                    "SELECT * FROM concepts WHERE session_id = ? ORDER BY position", (session_id,)
                )
            ]

            questions = [
                QuizQuestionPrivate(
                    id=r["id"],
                    concept_id=r["concept_id"],
                    question=r["question"],
                    options=json.loads(r["options"]),
                    explanation=r["explanation"],
                    correct_index=r["correct_index"],
                )
                for r in conn.execute(
                    "SELECT * FROM questions WHERE session_id = ? ORDER BY position", (session_id,)
                )
            ]

            latest = conn.execute(
                "SELECT results FROM attempts WHERE session_id = ? ORDER BY id DESC LIMIT 1",
                (session_id,),
            ).fetchone()
            results = ResultsResponse.model_validate_json(latest["results"]) if latest else None

            return LearningSession(
                id=row["id"],
                document_name=row["document_name"],
                file_hash=row["file_hash"],
                created_at=datetime.fromisoformat(row["created_at"]),
                status=row["status"],
                concepts=concepts,
                questions=questions,
                results=results,
            )

    def get_attempts(self, session_id):
        with self._conn() as conn:
            self._require_row(conn, session_id)
            rows = conn.execute(
                "SELECT results FROM attempts WHERE session_id = ? ORDER BY id", (session_id,)
            ).fetchall()
            return [ResultsResponse.model_validate_json(r["results"]) for r in rows]

    def find_by_file_hash(self, file_hash):
        placeholders = ",".join("?" for _ in CACHEABLE_STATUSES)
        with self._conn() as conn:
            row = conn.execute(
                f"SELECT id FROM sessions WHERE file_hash = ? AND status IN ({placeholders}) "
                "ORDER BY created_at DESC LIMIT 1",
                (file_hash, *CACHEABLE_STATUSES),
            ).fetchone()
        return self.get_session(row["id"]) if row else None


# ======================================================================
# Factory
# ======================================================================

@lru_cache(maxsize=1)
def get_store() -> SessionStore:
    """The app-wide store, chosen by STORE_BACKEND ('sqlite' default, or 'memory')."""
    backend = os.getenv("STORE_BACKEND", "sqlite").strip().lower()
    if backend == "memory":
        return InMemoryStore()
    if backend == "sqlite":
        return SqliteStore(os.getenv("DB_PATH", "conceptgraph.db"))
    raise ValueError(f"Unknown STORE_BACKEND '{backend}' (use 'sqlite' or 'memory')")
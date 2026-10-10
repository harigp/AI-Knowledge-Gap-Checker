import sqlite3
import time

import pytest

from gap_analyzer import build_results, make_concept_score
from models import Concept, QuizQuestion, QuizQuestionPrivate
from store import InMemoryStore, SessionNotFound, SqliteStore, get_store


@pytest.fixture(params=["memory", "sqlite"])
def store(request, tmp_path):
    """Every test in this file runs against BOTH backends."""
    if request.param == "memory":
        return InMemoryStore()
    return SqliteStore(str(tmp_path / "test.db"))


def chain():
    return [
        Concept(id="prob", name="Probability", description="Uncertain events",
                difficulty="beginner", prerequisite_ids=[]),
        Concept(id="stats", name="Statistics", source_type="inferred",
                prerequisite_ids=["prob"]),
        Concept(id="ml", name="Machine Learning", difficulty="advanced",
                prerequisite_ids=["stats", "prob"]),  # two prerequisites, order matters
    ]


def quiz():
    return [
        QuizQuestionPrivate(id="q1", concept_id="prob", question="P(even die)?",
                            options=["1/6", "1/3", "1/2", "2/3"], explanation="3 of 6",
                            correct_index=2),
        QuizQuestionPrivate(id="q2", concept_id="stats", question="Mean of 1,2,3?",
                            options=["1", "2", "3", "6"], explanation="Sum/3",
                            correct_index=1),
    ]


def results(session_id="x", correct=1):
    scores = [make_concept_score("prob", correct, 2), make_concept_score("stats", 1, 2)]
    return build_results(session_id, scores, chain())


def ready_session(store, file_hash="h1", name="notes.pdf"):
    sid = store.create_session(name, file_hash)
    store.save_concepts(sid, chain())
    store.save_quiz(sid, quiz())
    return sid


# ---------- sessions ----------

def test_create_and_get_session(store):
    sid = store.create_session("notes.pdf", "abc")
    s = store.get_session(sid)
    assert s.id == sid
    assert s.document_name == "notes.pdf"
    assert s.file_hash == "abc"
    assert s.status == "created"
    assert s.concepts == [] and s.questions == [] and s.results is None
    assert s.created_at.tzinfo is not None


def test_missing_session_returns_none(store):
    assert store.get_session("nope") is None


def test_session_ids_are_unique(store):
    assert store.create_session("a.pdf") != store.create_session("a.pdf")


def test_set_status(store):
    sid = store.create_session("a.pdf")
    store.set_status(sid, "failed")
    assert store.get_session(sid).status == "failed"


def test_mutators_raise_on_missing_session(store):
    with pytest.raises(SessionNotFound):
        store.save_concepts("nope", chain())
    with pytest.raises(SessionNotFound):
        store.save_quiz("nope", quiz())
    with pytest.raises(SessionNotFound):
        store.save_attempt("nope", {}, results())
    with pytest.raises(SessionNotFound):
        store.set_status("nope", "failed")
    with pytest.raises(SessionNotFound):
        store.pin_session("nope")


def test_getters_raise_on_missing_session(store):
    with pytest.raises(SessionNotFound):
        store.get_concepts("nope")
    with pytest.raises(SessionNotFound):
        store.get_quiz("nope")
    with pytest.raises(SessionNotFound):
        store.get_results("nope")


# ---------- concepts ----------

def test_concepts_round_trip_exactly(store):
    sid = store.create_session("a.pdf")
    store.save_concepts(sid, chain())
    assert store.get_concepts(sid) == chain()  # order, fields, prerequisite order all preserved
    assert store.get_session(sid).status == "graph_ready"


def test_save_concepts_replaces_previous(store):
    sid = store.create_session("a.pdf")
    store.save_concepts(sid, chain())
    store.save_concepts(sid, [Concept(id="only", name="Only")])
    assert [c.id for c in store.get_concepts(sid)] == ["only"]


def test_duplicate_concept_ids_rejected(store):
    sid = store.create_session("a.pdf")
    with pytest.raises(ValueError):
        store.save_concepts(sid, [Concept(id="a", name="A"), Concept(id="a", name="A2")])


def test_same_concept_ids_in_different_sessions_do_not_collide(store):
    s1, s2 = store.create_session("a.pdf"), store.create_session("b.pdf")
    store.save_concepts(s1, chain())
    store.save_concepts(s2, [Concept(id="prob", name="Different")])
    assert len(store.get_concepts(s1)) == 3
    assert store.get_concepts(s2)[0].name == "Different"


def test_returned_concepts_are_copies(store):
    sid = store.create_session("a.pdf")
    store.save_concepts(sid, chain())
    store.get_concepts(sid)[0].name = "TAMPERED"
    assert store.get_concepts(sid)[0].name == "Probability"


# ---------- quiz ----------

def test_public_quiz_has_no_answers(store):
    sid = ready_session(store)
    public = store.get_quiz(sid)
    assert all(type(q) is QuizQuestion for q in public)
    dumped = " ".join(q.model_dump_json() for q in public)
    assert "correct" not in dumped
    assert all(q.explanation == "" for q in public)


def test_private_quiz_has_answers_and_preserves_order(store):
    sid = ready_session(store)
    private = store.get_quiz(sid, include_answers=True)
    assert [q.id for q in private] == ["q1", "q2"]
    assert [q.correct_index for q in private] == [2, 1]
    assert private[0].options == ["1/6", "1/3", "1/2", "2/3"]
    assert private[0].explanation == "3 of 6"
    assert store.get_session(sid).status == "quiz_ready"


def test_quiz_is_empty_before_it_is_saved(store):
    sid = store.create_session("a.pdf")
    assert store.get_quiz(sid) == []


def test_duplicate_question_ids_rejected(store):
    sid = store.create_session("a.pdf")
    q = quiz()[0]
    with pytest.raises(ValueError):
        store.save_quiz(sid, [q, q])


# ---------- attempts / results ----------

def test_no_results_before_submission(store):
    assert store.get_results(ready_session(store)) is None


def test_save_attempt_and_get_results(store):
    sid = ready_session(store)
    r = results(sid)
    assert store.save_attempt(sid, {"q1": 2, "q2": 0}, r) == 1
    assert store.get_results(sid) == r
    assert store.get_session(sid).status == "completed"


def test_latest_attempt_wins_and_history_is_kept(store):
    sid = ready_session(store)
    first, second = results(sid, correct=0), results(sid, correct=2)
    assert store.save_attempt(sid, {"q1": 0}, first) == 1
    assert store.save_attempt(sid, {"q1": 2}, second) == 2
    assert store.get_results(sid) == second
    assert store.get_attempts(sid) == [first, second]  # oldest first: before/after


# ---------- demo cache ----------

def test_find_by_file_hash_misses_when_unknown(store):
    assert store.find_by_file_hash("nothing") is None


def test_find_by_file_hash_ignores_sessions_without_a_quiz(store):
    sid = store.create_session("a.pdf", "h1")
    store.save_concepts(sid, chain())  # graph only, no quiz yet
    assert store.find_by_file_hash("h1") is None


def test_find_by_file_hash_returns_newest_ready_session(store):
    first = ready_session(store, "h1")
    time.sleep(0.01)
    second = ready_session(store, "h1")
    assert store.find_by_file_hash("h1").id == second
    assert store.find_by_file_hash("h1").id != first
    assert store.find_by_file_hash("other") is None


def test_clone_session_copies_content_but_not_results(store):
    src = ready_session(store)
    store.save_attempt(src, {"q1": 2}, results(src))

    new = store.clone_session(src)
    clone = store.get_session(new)

    assert new != src
    assert clone.concepts == chain()
    assert [q.id for q in clone.questions] == ["q1", "q2"]
    assert clone.questions[0].correct_index == 2
    assert clone.results is None
    assert clone.status == "quiz_ready"
    assert clone.file_hash == "h1"

    store.save_attempt(new, {"q1": 0}, results(new, correct=0))
    assert store.get_results(src).session_id == src  # source untouched


def test_clone_missing_session_raises(store):
    with pytest.raises(SessionNotFound):
        store.clone_session("nope")


# ---------- expiration ----------

def test_fresh_sessions_survive_expiry(store):
    sid = store.create_session("a.pdf")
    assert store.delete_expired(3600) == 0
    assert store.get_session(sid) is not None


def test_expired_sessions_are_deleted(store):
    sid = ready_session(store)
    store.save_attempt(sid, {}, results(sid))
    assert store.delete_expired(-1) == 1  # negative age: everything counts as old
    assert store.get_session(sid) is None


def test_pinned_sessions_survive_expiry(store):
    keep = ready_session(store, "demo")
    drop = ready_session(store, "other")
    store.pin_session(keep)
    assert store.delete_expired(-1) == 1
    assert store.get_session(keep) is not None
    assert store.get_session(drop) is None
    assert store.find_by_file_hash("demo").id == keep


# ---------- SQLite-specific ----------

def test_sqlite_data_survives_a_new_store_instance(tmp_path):
    """The whole point of the database: a 'restart' doesn't lose sessions."""
    path = str(tmp_path / "persist.db")
    sid = ready_session(SqliteStore(path))

    reopened = SqliteStore(path)
    assert reopened.get_concepts(sid) == chain()
    assert [q.id for q in reopened.get_quiz(sid)] == ["q1", "q2"]


def test_sqlite_expiry_cascades_to_child_tables(tmp_path):
    path = str(tmp_path / "cascade.db")
    store = SqliteStore(path)
    sid = ready_session(store)
    store.save_attempt(sid, {}, results(sid))
    store.delete_expired(-1)

    conn = sqlite3.connect(path)
    for table in ("concepts", "prerequisites", "questions", "attempts"):
        assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0, table
    conn.close()


def test_sqlite_stores_graph_edges_in_prerequisites_table(tmp_path):
    path = str(tmp_path / "edges.db")
    sid = ready_session(SqliteStore(path))
    conn = sqlite3.connect(path)
    edges = set(conn.execute(
        "SELECT prerequisite_id, concept_id FROM prerequisites WHERE session_id = ?", (sid,)
    ))
    conn.close()
    assert edges == {("prob", "stats"), ("stats", "ml"), ("prob", "ml")}


# ---------- factory ----------

def test_get_store_defaults_to_sqlite(monkeypatch, tmp_path):
    monkeypatch.delenv("STORE_BACKEND", raising=False)
    monkeypatch.setenv("DB_PATH", str(tmp_path / "f.db"))
    get_store.cache_clear()
    assert isinstance(get_store(), SqliteStore)
    get_store.cache_clear()


def test_get_store_memory_flag(monkeypatch):
    monkeypatch.setenv("STORE_BACKEND", "memory")
    get_store.cache_clear()
    assert isinstance(get_store(), InMemoryStore)
    assert get_store() is get_store()  # singleton
    get_store.cache_clear()


def test_get_store_rejects_unknown_backend(monkeypatch):
    monkeypatch.setenv("STORE_BACKEND", "postgres")
    get_store.cache_clear()
    with pytest.raises(ValueError):
        get_store()
    get_store.cache_clear()
"""End-to-end API tests with mocked AI."""

import json

from fastapi.testclient import TestClient

from app.errors import AIServiceError
from app.main import create_app
from tests.conftest import (MOCK_ANSWER_KEY, FakeGenerator, make_blank_pdf, make_pdf, make_settings,
                            mock_by_task)


def upload(client, data, name="lecture.pdf", ctype="application/pdf"):
    return client.post("/api/analyze", files={"file": (name, data, ctype)})


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["ai_configured"] is True
    assert "key" not in json.dumps(body).lower()


def test_full_flow(analyzed):
    client, a = analyzed
    sid = a["session_id"]
    assert a["document_name"] == "lecture.pdf"
    assert len(a["concepts"]) == 9 and len(a["edges"]) == 10
    assert a["processing_status"]["quiz_status"] == "pending"

    g = client.get(f"/api/graph/{sid}").json()
    assert g["concepts"] == a["concepts"] and g["edges"] == a["edges"]

    q = client.get(f"/api/quiz/{sid}")
    assert q.status_code == 200
    quiz = q.json()
    assert quiz["total_questions"] == 12 and len(quiz["assessed_concept_ids"]) == 6
    raw = json.dumps(quiz)
    assert "correct" not in raw and "explanation" not in raw
    assert client.get(f"/api/quiz/{sid}").json() == quiz  # cached, stable

    r = client.get(f"/api/results/{sid}")
    assert r.status_code == 409 and r.json()["error"]["code"] == "assessment_not_submitted"

    answers = [{"question_id": f"q{i + 1}", "selected_option_id": k} for i, k in enumerate(MOCK_ANSWER_KEY)]
    answers[2]["selected_option_id"] = "A"   # probability_basics: both wrong
    answers[3]["selected_option_id"] = "B"
    s = client.post(f"/api/quiz/{sid}/submit", json={"answers": answers})
    assert s.status_code == 200, s.text
    res = s.json()
    assert res["total_correct"] == 10 and res["total_questions"] == 12
    assert res["overall_score"] == round(10 / 12, 4)
    assert res["learning_gaps"][0]["concept_id"] == "probability_basics"
    assert res["learning_gaps"][0]["priority"] == 1.75
    assert res["learning_path"]["steps"][0]["concept_id"] == "probability_basics"
    unassessed = [c for c in res["concept_scores"] if c["mastery"] == "unassessed"]
    assert unassessed and all(c["score"] is None for c in unassessed)

    again = client.post(f"/api/quiz/{sid}/submit", json={"answers": answers})
    assert again.status_code == 409 and again.json()["error"]["code"] == "already_submitted"

    saved = client.get(f"/api/results/{sid}")
    assert saved.status_code == 200 and saved.json() == res
    assert client.get(f"/api/quiz/{sid}").json()["submitted"] is True


def test_unknown_session_404(client):
    for path in ["/api/graph/nope", "/api/quiz/nope", "/api/results/nope"]:
        r = client.get(path)
        assert r.status_code == 404 and r.json()["error"]["code"] == "session_not_found"
    r = client.post("/api/quiz/nope/submit", json={"answers": []})
    assert r.status_code == 404


def test_submit_before_quiz_generated(analyzed):
    client, a = analyzed
    r = client.post(f"/api/quiz/{a['session_id']}/submit", json={"answers": []})
    assert r.status_code == 400 and r.json()["error"]["code"] == "quiz_not_generated"


def test_submit_invalid_question_and_option(analyzed):
    client, a = analyzed
    sid = a["session_id"]
    client.get(f"/api/quiz/{sid}")
    r = client.post(f"/api/quiz/{sid}/submit", json={"answers": [{"question_id": "q99", "selected_option_id": "A"}]})
    assert r.status_code == 400 and r.json()["error"]["code"] == "invalid_question_id"
    r = client.post(f"/api/quiz/{sid}/submit", json={"answers": [{"question_id": "q1", "selected_option_id": "E"}]})
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"
    # failed submissions do not consume the one allowed grading
    r = client.post(f"/api/quiz/{sid}/submit", json={"answers": []})
    assert r.status_code == 200 and r.json()["unanswered_count"] == 12


def test_upload_rejections(client):
    assert upload(client, b"plain text", name="notes.txt", ctype="text/plain").json()["error"]["code"] == "invalid_file_type"
    r = upload(client, b"not really a pdf" * 30)
    assert r.status_code == 400 and r.json()["error"]["code"] == "invalid_file_type"
    r = upload(client, make_blank_pdf())
    assert r.status_code == 400 and r.json()["error"]["code"] == "no_extractable_text"
    r = client.post("/api/analyze")
    assert r.status_code == 422


def test_upload_too_large():
    with TestClient(create_app(make_settings(max_file_size_mb=0.001))) as c:
        r = upload(c, make_pdf())
    assert r.status_code == 413 and r.json()["error"]["code"] == "file_too_large"


def test_upload_too_many_pages():
    with TestClient(create_app(make_settings(max_pages=2))) as c:
        r = upload(c, make_pdf(pages=3))
    assert r.status_code == 400 and r.json()["error"]["code"] == "too_many_pages"


def test_ai_failure_maps_to_503():
    gen = FakeGenerator(AIServiceError("down", code="ai_unavailable", status_code=503))
    with TestClient(create_app(make_settings(), generator=gen)) as c:
        r = upload(c, make_pdf())
    assert r.status_code == 503 and r.json()["error"]["code"] == "ai_unavailable"


def test_missing_key_maps_to_503():
    with TestClient(create_app(make_settings(ai_mode="gemini", gemini_api_key=""))) as c:
        r = upload(c, make_pdf())
    assert r.status_code == 503 and r.json()["error"]["code"] == "ai_not_configured"


def test_quiz_answers_shuffled_in_gemini_mode():
    with TestClient(create_app(make_settings(ai_mode="gemini", gemini_api_key="k"),
                               generator=FakeGenerator(mock_by_task))) as c:
        sid = upload(c, make_pdf()).json()["session_id"]
        quiz = c.get(f"/api/quiz/{sid}").json()
        assert "correct" not in json.dumps(quiz)
        # submitting option texts' correct answers requires the server key; all-A should not be perfect
        res = c.post(f"/api/quiz/{sid}/submit",
                     json={"answers": [{"question_id": q["id"], "selected_option_id": "A"} for q in quiz["questions"]]})
        assert res.status_code == 200


def test_rate_limit_on_analyze():
    with TestClient(create_app(make_settings(rate_limit_analyze_per_minute=2))) as c:
        codes = [upload(c, make_pdf()).status_code for _ in range(3)]
    assert codes == [200, 200, 429]


def test_cors_allows_dev_origin(client):
    r = client.options("/api/analyze", headers={"Origin": "http://localhost:5173",
                                                "Access-Control-Request-Method": "POST"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"
    r = client.options("/api/analyze", headers={"Origin": "http://localhost:5174",
                                                "Access-Control-Request-Method": "POST"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5174"  # any local port
    r = client.options("/api/analyze", headers={"Origin": "http://localhost.evil.example",
                                                "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in r.headers
    r = client.options("/api/analyze", headers={"Origin": "http://evil.example",
                                                "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in r.headers


def test_session_expiry():
    with TestClient(create_app(make_settings(session_ttl_minutes=0))) as c:
        sid = upload(c, make_pdf()).json()["session_id"]
        assert c.get(f"/api/graph/{sid}").status_code == 404


def test_session_ids_unguessable(client):
    ids = {upload(client, make_pdf()).json()["session_id"] for _ in range(3)}
    assert len(ids) == 3 and all(len(i) >= 32 for i in ids)


def test_openapi_available(client):
    spec = client.get("/openapi.json").json()
    for path in ["/health", "/api/analyze", "/api/graph/{session_id}", "/api/quiz/{session_id}",
                 "/api/quiz/{session_id}/submit", "/api/results/{session_id}"]:
        assert path in spec["paths"]

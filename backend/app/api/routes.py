"""REST endpoints. Response shapes are defined in app.models and documented in API_CONTRACT.md."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, Request, UploadFile
from fastapi.concurrency import run_in_threadpool

from app.errors import ConflictError, FileTooLargeError, InvalidInputError
from app.models import (AnalyzeResponse, AssessmentResults, ErrorResponse, GraphResponse, HealthResponse, QuizResponse,
                        QuizSubmitRequest)
from app.rate_limit import client_key
from app.services import gap_service, graph_service, pdf_service, quiz_service
from app.services.learning_path_service import build_learning_path
from app.services.session_service import Session, utcnow

logger = logging.getLogger("conceptgraph.api")


def _errors(*codes: int) -> dict:
    return {code: {"model": ErrorResponse} for code in codes}


def default_rate_limit(request: Request) -> None:
    state = request.app.state
    state.limiter.check(f"default:{client_key(request)}", state.settings.rate_limit_default_per_minute)


router = APIRouter()
api = APIRouter(prefix="/api", dependencies=[Depends(default_rate_limit)])


@router.get("/health", response_model=HealthResponse, tags=["health"])
async def health(request: Request) -> dict:
    s = request.app.state.settings
    return {"status": "ok", "service": "conceptgraph-backend", "version": s.app_version,
            "ai_configured": s.ai_configured, "timestamp": utcnow()}


# ---------------------------------------------------------------------------
# Analyze
# ---------------------------------------------------------------------------
@api.post("/analyze", response_model=AnalyzeResponse, tags=["analysis"],
          responses=_errors(400, 413, 422, 429, 500, 502, 503),
          summary="Upload a PDF and build its concept graph")
async def analyze(request: Request, file: UploadFile = File(..., description="Lecture notes PDF (max 10 MB, 50 pages)")) -> dict:
    state = request.app.state
    settings = state.settings
    state.limiter.check(f"analyze:{client_key(request)}", settings.rate_limit_analyze_per_minute)

    pdf_service.validate_upload_metadata(file.filename, file.content_type)
    data = await file.read(settings.max_file_size_bytes + 1)
    if len(data) > settings.max_file_size_bytes:
        raise FileTooLargeError(f"File exceeds the {settings.max_file_size_mb:g} MB limit.",
                                details={"max_bytes": settings.max_file_size_bytes})
    document = await run_in_threadpool(pdf_service.extract_text, data, settings)
    del data  # never keep the original PDF

    extraction = await state.ai.extract_concepts(document.text, document.estimated_tokens)
    graph = graph_service.serialize_graph(extraction.concepts)
    quiz_context = document.text[: settings.quiz_context_tokens * 4]
    document_name = (file.filename or "document.pdf").replace("\\", "/").split("/")[-1][:200]
    session = state.sessions.create(document_name, extraction.concepts, quiz_context)
    logger.info("Analyzed document: pages=%d tokens=%d mode=%s concepts=%d requests=%d",
                document.page_count, document.estimated_tokens, extraction.processing_mode,
                len(extraction.concepts), extraction.requests_used)

    return {
        "session_id": session.id,
        "document_name": session.document_name,
        **graph,
        "processing_status": {
            "status": "completed",
            "processing_mode": extraction.processing_mode,
            "page_count": document.page_count,
            "estimated_tokens": document.estimated_tokens,
            "chunk_count": extraction.chunk_count,
            "concept_count": len(extraction.concepts),
            "ai_requests_used": extraction.requests_used,
            "quiz_status": "pending",
            "warnings": extraction.warnings,
        },
        "expires_at": session.expires_at,
    }


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------
@api.get("/graph/{session_id}", response_model=GraphResponse, tags=["analysis"], responses=_errors(404, 422, 429))
async def get_graph(session_id: str, request: Request) -> dict:
    session = request.app.state.sessions.get(session_id)
    return {"session_id": session.id, "document_name": session.document_name,
            **graph_service.serialize_graph(session.concepts)}


# ---------------------------------------------------------------------------
# Quiz
# ---------------------------------------------------------------------------
async def _ensure_quiz(request: Request, session: Session) -> None:
    """Generate the quiz once per session (callers must hold session.lock)."""
    if session.questions is not None:
        return
    state = request.app.state
    s = state.settings
    selected = quiz_service.select_quiz_concepts(session.concepts, s.quiz_min_concepts, s.quiz_max_concepts)
    generated = await state.ai.generate_quiz(selected, session.quiz_context)
    session.questions = quiz_service.store_questions(generated)
    session.quiz_context = None  # document excerpt no longer needed


@api.get("/quiz/{session_id}", response_model=QuizResponse, tags=["quiz"],
         responses=_errors(404, 422, 429, 502, 503),
         summary="Get the diagnostic quiz (answers excluded); generated on first call")
async def get_quiz(session_id: str, request: Request) -> dict:
    session = request.app.state.sessions.get(session_id)
    async with session.lock:
        await _ensure_quiz(request, session)
        questions = session.questions
        submitted = session.results is not None
    return {
        "session_id": session.id,
        "total_questions": len(questions),
        "assessed_concept_ids": list(dict.fromkeys(q.concept_id for q in questions)),
        "submitted": submitted,
        "questions": quiz_service.public_questions(questions, session.concepts),
    }


@api.post("/quiz/{session_id}/submit", response_model=AssessmentResults, tags=["quiz"],
          responses=_errors(400, 404, 409, 422, 429),
          summary="Submit answers; returns scores, gaps, recommendations and learning path")
async def submit_quiz(session_id: str, body: QuizSubmitRequest, request: Request) -> dict:
    state = request.app.state
    session = state.sessions.get(session_id)
    async with session.lock:
        if session.results is not None:
            raise ConflictError("This quiz has already been submitted. Fetch /api/results instead.",
                                code="already_submitted")
        if session.questions is None:
            raise InvalidInputError("Fetch the quiz before submitting answers.", code="quiz_not_generated")

        graded = quiz_service.grade(session.questions,
                                    [(a.question_id, a.selected_option_id) for a in body.answers])
        s = state.settings
        cfg = gap_service.GapConfig(s.strong_threshold, s.developing_threshold, s.descendant_weight)
        analysis = gap_service.analyze(session.concepts, graded.concept_tallies, cfg)
        results = {
            "session_id": session.id,
            "submitted_at": utcnow(),
            "overall_score": graded.overall_score,
            "total_correct": graded.total_correct,
            "total_questions": graded.total_questions,
            "unanswered_count": graded.unanswered_count,
            "concept_scores": analysis.concept_scores,
            "question_results": graded.question_results,
            "learning_gaps": analysis.learning_gaps,
            "recommendations": analysis.recommendations,
            "learning_path": build_learning_path(session.concepts, analysis),
        }
        session.results = results
    return results


@api.get("/results/{session_id}", response_model=AssessmentResults, tags=["quiz"], responses=_errors(404, 409, 422, 429))
async def get_results(session_id: str, request: Request) -> dict:
    session = request.app.state.sessions.get(session_id)
    if session.results is None:
        raise ConflictError("No assessment has been submitted for this session yet.",
                            code="assessment_not_submitted")
    return session.results

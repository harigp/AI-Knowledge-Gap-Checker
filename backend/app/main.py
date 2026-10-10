"""FastAPI application factory.

Run locally:  uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import api, router
from app.config import Settings, get_settings
from app.errors import register_error_handlers
from app.rate_limit import RateLimiter
from app.services.ai_service import AIService
from app.services.gemini_client import GeminiJsonGenerator, JsonGenerator
from app.services.mock_ai import MockJsonGenerator
from app.services.session_service import SessionStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

DESCRIPTION = """Backend for **ConceptGraph AI** — an AI-powered knowledge gap detector.

Upload lecture notes → get a prerequisite concept graph → take a diagnostic quiz →
receive explainable knowledge gaps and a prerequisite-ordered learning path.

All errors use the envelope `{"error": {"code", "message", "details"}}`. See API_CONTRACT.md.
"""


def create_app(settings: Settings | None = None, generator: JsonGenerator | None = None) -> FastAPI:
    settings = settings or get_settings()
    if generator is None:
        generator = MockJsonGenerator() if settings.ai_mode == "mock" else GeminiJsonGenerator(settings)

    app = FastAPI(title="ConceptGraph AI API", version=settings.app_version, description=DESCRIPTION)
    app.state.settings = settings
    app.state.sessions = SessionStore(settings.session_ttl_minutes, settings.max_sessions)
    app.state.ai = AIService(generator, settings, shuffle_options=settings.ai_mode != "mock")
    app.state.limiter = RateLimiter()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=settings.cors_origin_regex or None,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type"],
    )
    register_error_handlers(app)
    app.include_router(router)
    app.include_router(api)

    if settings.ai_mode == "mock":
        logging.getLogger("conceptgraph").warning("AI_MODE=mock: returning canned concepts and quiz.")
    elif not settings.gemini_api_key:
        logging.getLogger("conceptgraph").warning("GEMINI_API_KEY is not set; /api/analyze will return 503.")
    return app


app = create_app()

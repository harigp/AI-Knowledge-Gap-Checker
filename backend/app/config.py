"""Application configuration loaded from environment variables (and backend/.env)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BACKEND_DIR / ".env")


def _int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value not in (None, "") else default


def _float(name: str, default: float) -> float:
    value = os.getenv(name)
    return float(value) if value not in (None, "") else default


def _list(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_version: str = "1.0.0"

    # AI
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    gemini_model: str = field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    # Used when the primary model times out, is overloaded (5xx) or rate limited (429). "" disables.
    gemini_fallback_model: str = field(default_factory=lambda: os.getenv("GEMINI_FALLBACK_MODEL", "gemini-2.5-flash-lite"))
    # Gemini 3.x models: thinking level ("minimal"/"low"/"medium"/"high"; "" = model default).
    gemini_thinking_level: str = field(default_factory=lambda: os.getenv("GEMINI_THINKING_LEVEL", "low"))
    # Gemini 2.x models: thinking token budget (0 = off, -1 = model default).
    gemini_thinking_budget: int = field(default_factory=lambda: _int("GEMINI_THINKING_BUDGET", 0))
    # "gemini" calls the real API; "mock" returns canned data (no key needed, for frontend dev).
    ai_mode: str = field(default_factory=lambda: os.getenv("AI_MODE", "gemini").lower())
    gemini_timeout_seconds: float = field(default_factory=lambda: _float("GEMINI_TIMEOUT_SECONDS", 45.0))
    gemini_max_retries: int = field(default_factory=lambda: _int("GEMINI_MAX_RETRIES", 2))
    gemini_max_concurrency: int = field(default_factory=lambda: _int("GEMINI_MAX_CONCURRENCY", 2))
    max_ai_requests_per_document: int = field(default_factory=lambda: _int("MAX_AI_REQUESTS_PER_DOCUMENT", 12))

    # PDF limits
    max_file_size_mb: float = field(default_factory=lambda: _float("MAX_FILE_SIZE_MB", 10.0))
    max_pages: int = field(default_factory=lambda: _int("MAX_PAGES", 50))
    min_text_chars: int = field(default_factory=lambda: _int("MIN_TEXT_CHARS", 200))

    # Token budgeting
    direct_token_threshold: int = field(default_factory=lambda: _int("DIRECT_TOKEN_THRESHOLD", 15000))
    chunk_target_tokens: int = field(default_factory=lambda: _int("CHUNK_TARGET_TOKENS", 4000))
    chunk_overlap_tokens: int = field(default_factory=lambda: _int("CHUNK_OVERLAP_TOKENS", 200))
    max_chunks: int = field(default_factory=lambda: _int("MAX_CHUNKS", 10))
    max_document_tokens: int = field(default_factory=lambda: _int("MAX_DOCUMENT_TOKENS", 40000))
    quiz_context_tokens: int = field(default_factory=lambda: _int("QUIZ_CONTEXT_TOKENS", 6000))

    # Concepts / quiz
    min_concepts: int = field(default_factory=lambda: _int("MIN_CONCEPTS", 3))
    max_concepts: int = field(default_factory=lambda: _int("MAX_CONCEPTS", 15))
    quiz_min_concepts: int = field(default_factory=lambda: _int("QUIZ_MIN_CONCEPTS", 4))
    quiz_max_concepts: int = field(default_factory=lambda: _int("QUIZ_MAX_CONCEPTS", 6))
    questions_per_concept: int = field(default_factory=lambda: _int("QUESTIONS_PER_CONCEPT", 2))

    # Gap analysis
    strong_threshold: float = field(default_factory=lambda: _float("MASTERY_STRONG_THRESHOLD", 0.80))
    developing_threshold: float = field(default_factory=lambda: _float("MASTERY_DEVELOPING_THRESHOLD", 0.50))
    descendant_weight: float = field(default_factory=lambda: _float("PRIORITY_DESCENDANT_WEIGHT", 0.25))

    # Sessions
    session_ttl_minutes: int = field(default_factory=lambda: _int("SESSION_TTL_MINUTES", 120))
    max_sessions: int = field(default_factory=lambda: _int("MAX_SESSIONS", 500))

    # HTTP
    cors_origins: list[str] = field(
        default_factory=lambda: _list("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")
    )
    rate_limit_analyze_per_minute: int = field(default_factory=lambda: _int("RATE_LIMIT_ANALYZE_PER_MINUTE", 5))
    rate_limit_default_per_minute: int = field(default_factory=lambda: _int("RATE_LIMIT_DEFAULT_PER_MINUTE", 120))

    @property
    def max_file_size_bytes(self) -> int:
        return int(self.max_file_size_mb * 1024 * 1024)

    @property
    def ai_configured(self) -> bool:
        return self.ai_mode == "mock" or bool(self.gemini_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()

"""Application errors and the consistent JSON error envelope.

Every error response has the shape:
    {"error": {"code": "<machine_code>", "message": "<human message>", "details": {...} | null}}
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("conceptgraph")


class AppError(Exception):
    status_code = 400
    code = "bad_request"

    def __init__(self, message: str, *, code: str | None = None, status_code: int | None = None,
                 details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code
        self.details = details


class InvalidInputError(AppError):
    status_code = 400
    code = "invalid_input"


class FileTooLargeError(AppError):
    status_code = 413
    code = "file_too_large"


class SessionNotFoundError(AppError):
    status_code = 404
    code = "session_not_found"

    def __init__(self) -> None:
        super().__init__("Session not found or expired. Upload the document again.")


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


class RateLimitError(AppError):
    status_code = 429
    code = "rate_limited"


class AIServiceError(AppError):
    """AI provider failed (unavailable, timed out, or returned unusable output)."""

    status_code = 503
    code = "ai_unavailable"


class GraphValidationError(AppError):
    status_code = 422
    code = "invalid_graph"


def error_body(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"error": {"code": code, "message": message, "details": details}}


_HTTP_CODES = {400: "invalid_input", 404: "not_found", 405: "method_not_allowed", 413: "file_too_large",
               429: "rate_limited"}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        headers = {"Retry-After": "60"} if exc.status_code == 429 else None
        return JSONResponse(error_body(exc.code, exc.message, exc.details), status_code=exc.status_code,
                            headers=headers)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [{"loc": list(e.get("loc", [])), "msg": e.get("msg", ""), "type": e.get("type", "")}
                  for e in exc.errors()]
        return JSONResponse(error_body("validation_error", "Request validation failed.", {"errors": errors}),
                            status_code=422)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _HTTP_CODES.get(exc.status_code, "http_error")
        return JSONResponse(error_body(code, str(exc.detail)), status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def _unexpected(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unexpected error: %s", type(exc).__name__)
        return JSONResponse(error_body("internal_error", "An unexpected error occurred."), status_code=500)

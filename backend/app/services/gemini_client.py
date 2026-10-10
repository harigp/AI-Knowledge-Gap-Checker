"""Low-level Gemini transport: structured JSON generation with timeout, retries and a
concurrency cap. Maps provider failures onto AIServiceError / RateLimitError."""

from __future__ import annotations

import asyncio
import logging
from typing import Protocol

from pydantic import BaseModel

from app.config import Settings
from app.errors import AIServiceError, RateLimitError

logger = logging.getLogger("conceptgraph.gemini")


class RequestBudget:
    """Counts AI requests made for one document/operation and enforces a ceiling."""

    def __init__(self, limit: int):
        self.limit = limit
        self.used = 0

    def consume(self) -> None:
        if self.used >= self.limit:
            raise AIServiceError("The AI request budget for this document was exhausted.",
                                 code="ai_budget_exceeded", status_code=503)
        self.used += 1


class JsonGenerator(Protocol):
    async def generate(self, *, task: str, system: str, prompt: str, schema: type[BaseModel],
                       budget: RequestBudget) -> str:
        """Return the model's raw JSON text for the given task."""
        ...


class GeminiJsonGenerator:
    def __init__(self, settings: Settings, client=None):
        self._settings = settings
        self._client = client
        self._semaphore = asyncio.Semaphore(settings.gemini_max_concurrency)

    def _get_client(self):
        if self._client is None:
            if not self._settings.gemini_api_key:
                raise AIServiceError("The AI service is not configured on the server.",
                                     code="ai_not_configured", status_code=503)
            from google import genai
            from google.genai import types

            self._client = genai.Client(
                api_key=self._settings.gemini_api_key,
                http_options=types.HttpOptions(timeout=int(self._settings.gemini_timeout_seconds * 1000)),
            )
        return self._client

    def _config(self, model: str, system: str, schema: type[BaseModel]):
        from google.genai import types

        kwargs = dict(
            system_instruction=system,
            response_mime_type="application/json",
            response_schema=schema,
            temperature=0.2,
        )
        # Gemini 2.x takes a thinking token budget; Gemini 3.x takes a thinking level.
        if model.startswith("gemini-2"):
            if self._settings.gemini_thinking_budget >= 0:
                kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=self._settings.gemini_thinking_budget)
        elif self._settings.gemini_thinking_level:
            kwargs["thinking_config"] = types.ThinkingConfig(thinking_level=self._settings.gemini_thinking_level)
        return types.GenerateContentConfig(**kwargs)

    async def generate(self, *, task: str, system: str, prompt: str, schema: type[BaseModel],
                       budget: RequestBudget) -> str:
        """Try the primary model; on a recoverable failure (timeout, 429, 5xx) switch to the fallback model
        immediately (if configured), which then gets the normal retry policy."""
        client = self._get_client()
        primary, fallback = self._settings.gemini_model, self._settings.gemini_fallback_model
        if fallback and fallback != primary:
            try:
                return await self._attempt(client, primary, task, system, prompt, schema, budget, attempts=1)
            except _Recoverable as exc:
                logger.warning("Gemini %s: primary model unavailable, failing over to fallback model", task)
                last = exc
            try:
                return await self._attempt(client, fallback, task, system, prompt, schema, budget,
                                           attempts=self._settings.gemini_max_retries + 1)
            except _Recoverable as exc:
                last = exc
        else:
            try:
                return await self._attempt(client, primary, task, system, prompt, schema, budget,
                                           attempts=self._settings.gemini_max_retries + 1)
            except _Recoverable as exc:
                last = exc
        raise _final_error(last.cause) from last.cause

    async def _attempt(self, client, model: str, task: str, system: str, prompt: str, schema: type[BaseModel],
                       budget: RequestBudget, attempts: int) -> str:
        """Call ``model`` up to ``attempts`` times. Raises _Recoverable when all attempts hit
        recoverable errors, AIServiceError for non-recoverable ones."""
        from google.genai import errors as genai_errors

        config = self._config(model, system, schema)
        last_error: Exception | None = None
        for attempt in range(1, attempts + 1):
            budget.consume()
            try:
                async with self._semaphore:
                    response = await asyncio.wait_for(
                        client.aio.models.generate_content(model=model, contents=prompt, config=config),
                        timeout=self._settings.gemini_timeout_seconds,
                    )
                text = response.text
                if text:
                    return text
                last_error = AIServiceError("The AI service returned an empty response.",
                                            code="ai_invalid_response", status_code=502)
                logger.warning("Gemini %s/%s returned empty output (attempt %d/%d)", model, task, attempt, attempts)
            except asyncio.TimeoutError as exc:
                last_error = exc
                logger.warning("Gemini %s/%s timed out (attempt %d/%d)", model, task, attempt, attempts)
            except genai_errors.APIError as exc:
                last_error = exc
                code = getattr(exc, "code", None) or 0
                logger.warning("Gemini %s/%s failed with HTTP %s (attempt %d/%d)", model, task, code, attempt,
                               attempts)
                if code in (401, 403):
                    raise AIServiceError("The AI service rejected the server's credentials.",
                                         code="ai_unavailable", status_code=503) from exc
                if code == 400:
                    raise AIServiceError("The AI service rejected the request.", code="ai_invalid_response",
                                         status_code=502) from exc
                if code != 429 and code < 500:
                    raise AIServiceError("The AI service request failed.", code="ai_unavailable",
                                         status_code=503) from exc
            except Exception as exc:  # network errors from httpx etc.
                last_error = exc
                logger.warning("Gemini %s/%s error %s (attempt %d/%d)", model, task, type(exc).__name__, attempt,
                               attempts)

            if attempt < attempts:
                await asyncio.sleep(min(2 ** (attempt - 1), 4))
        raise _Recoverable(last_error)


class _Recoverable(Exception):
    def __init__(self, cause: Exception | None):
        super().__init__(str(cause))
        self.cause = cause


def _final_error(cause: Exception | None) -> Exception:
    if isinstance(cause, AIServiceError):
        return cause
    if getattr(cause, "code", None) == 429:
        return RateLimitError("The AI service is rate limited. Please try again in a minute.", code="rate_limited")
    if isinstance(cause, asyncio.TimeoutError):
        return AIServiceError("The AI service timed out. Please try again.", code="ai_unavailable", status_code=503)
    return AIServiceError("The AI service is temporarily unavailable.", code="ai_unavailable", status_code=503)

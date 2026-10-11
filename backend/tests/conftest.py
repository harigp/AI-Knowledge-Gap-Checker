from __future__ import annotations

import dataclasses
import json
import os

# Never touch the real Gemini API from tests, regardless of the developer's .env.
os.environ["GEMINI_API_KEY"] = ""
os.environ["AI_MODE"] = "mock"

import pymupdf  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402
from app.services.mock_ai import MOCK_CONCEPTS, MOCK_QUESTIONS  # noqa: E402

LOREM = ("Linear regression models the relationship between a predictor and a response. "
         "The least squares method chooses coefficients that minimize squared residuals. ")
MOCK_ANSWER_KEY = "BDCABADCABCD"


def make_settings(**overrides) -> Settings:
    base = Settings(gemini_api_key="", ai_mode="mock", gemini_fallback_model_1="", gemini_fallback_model_2="", gemini_fallback_model_3="", gemini_fallback_model_4="", gemini_max_retries=2,
                    gemini_timeout_seconds=1.0, rate_limit_analyze_per_minute=1000,
                    rate_limit_default_per_minute=1000)
    return dataclasses.replace(base, **overrides)


def make_pdf(pages: int = 1, text: str = LOREM * 8) -> bytes:
    doc = pymupdf.open()
    for _ in range(pages):
        page = doc.new_page()
        page.insert_textbox(pymupdf.Rect(50, 50, 560, 800), text, fontsize=10)
    data = doc.tobytes()
    doc.close()
    return data


def make_blank_pdf(pages: int = 1) -> bytes:
    doc = pymupdf.open()
    for _ in range(pages):
        doc.new_page()
    data = doc.tobytes()
    doc.close()
    return data


def make_encrypted_pdf() -> bytes:
    doc = pymupdf.open()
    doc.new_page().insert_textbox(pymupdf.Rect(50, 50, 560, 800), LOREM * 8)
    data = doc.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="secret", owner_pw="owner")
    doc.close()
    return data


class FakeGenerator:
    """Scripted JsonGenerator: returns queued responses (str/dict) or raises queued exceptions."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls: list[dict] = []

    async def generate(self, *, task, system, prompt, schema, budget):
        budget.consume()
        self.calls.append({"task": task, "system": system, "prompt": prompt})
        item = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        if isinstance(item, Exception):
            raise item
        if callable(item):
            item = item(task)
        return item if isinstance(item, str) else json.dumps(item)


def mock_by_task(task: str) -> dict:
    return {"questions": MOCK_QUESTIONS} if task == "generate_quiz" else {"concepts": MOCK_CONCEPTS}


@pytest.fixture
def client():
    with TestClient(create_app(make_settings())) as c:
        yield c


@pytest.fixture
def analyzed(client):
    """A client plus a session that has been analyzed (mock AI)."""
    r = client.post("/api/analyze", files={"file": ("lecture.pdf", make_pdf(), "application/pdf")})
    assert r.status_code == 200, r.text
    return client, r.json()

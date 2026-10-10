"""PDF validation, text extraction, token estimation and chunking."""

from __future__ import annotations

import re
from dataclasses import dataclass

import pymupdf

from app.config import Settings
from app.errors import FileTooLargeError, InvalidInputError

PDF_MAGIC = b"%PDF-"


@dataclass
class ExtractedDocument:
    text: str
    page_count: int
    estimated_tokens: int


def estimate_tokens(text: str) -> int:
    """Approximate Gemini token count (~4 characters per token for English prose)."""
    return (len(text) + 3) // 4


def validate_upload_metadata(filename: str | None, content_type: str | None) -> None:
    name_ok = bool(filename) and filename.lower().endswith(".pdf")
    type_ok = (content_type or "").lower() in {"application/pdf", "application/x-pdf"}
    if not (name_ok or type_ok):
        raise InvalidInputError("Only PDF files are supported.", code="invalid_file_type")


def extract_text(data: bytes, settings: Settings) -> ExtractedDocument:
    """Validate PDF bytes and extract text. Raises InvalidInputError / FileTooLargeError."""
    if len(data) > settings.max_file_size_bytes:
        raise FileTooLargeError(f"File exceeds the {settings.max_file_size_mb:g} MB limit.",
                                details={"max_bytes": settings.max_file_size_bytes})
    if not data:
        raise InvalidInputError("The uploaded file is empty.", code="empty_pdf")
    if not data[:1024].lstrip().startswith(PDF_MAGIC):
        raise InvalidInputError("The file is not a valid PDF.", code="invalid_file_type")

    try:
        doc = pymupdf.open(stream=data, filetype="pdf")
    except Exception as exc:  # PyMuPDF raises various types for corrupt files
        raise InvalidInputError("The PDF is corrupted or unreadable.", code="invalid_pdf") from exc

    with doc:
        if doc.needs_pass and not doc.authenticate(""):
            raise InvalidInputError("Password-protected PDFs are not supported.", code="encrypted_pdf")
        page_count = doc.page_count
        if page_count == 0:
            raise InvalidInputError("The PDF has no pages.", code="empty_pdf")
        if page_count > settings.max_pages:
            raise InvalidInputError(f"The PDF has {page_count} pages; the limit is {settings.max_pages}.",
                                    code="too_many_pages",
                                    details={"max_pages": settings.max_pages, "page_count": page_count})
        try:
            pages = [page.get_text("text") for page in doc]
        except Exception as exc:
            raise InvalidInputError("The PDF is corrupted or unreadable.", code="invalid_pdf") from exc

    text = normalize_text("\n\n".join(pages))
    if len(re.sub(r"\s", "", text)) < settings.min_text_chars:
        raise InvalidInputError("No readable text found. Scanned or image-only PDFs are not supported.",
                                code="no_extractable_text")
    return ExtractedDocument(text=text, page_count=page_count, estimated_tokens=estimate_tokens(text))


def normalize_text(text: str) -> str:
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(text: str, target_tokens: int, overlap_tokens: int) -> list[str]:
    """Split text into ~target_tokens chunks on paragraph boundaries, with a small overlap.

    Paragraphs longer than the target are split on sentence boundaries, then hard-split.
    No text is dropped.
    """
    target_chars = target_tokens * 4
    overlap_chars = overlap_tokens * 4

    pieces: list[str] = []
    for para in (p.strip() for p in text.split("\n\n")):
        if not para:
            continue
        if len(para) <= target_chars:
            pieces.append(para)
            continue
        buf = ""
        for sentence in re.split(r"(?<=[.!?])\s+", para):
            while len(sentence) > target_chars:
                if buf:
                    pieces.append(buf)
                    buf = ""
                pieces.append(sentence[:target_chars])
                sentence = sentence[target_chars:]
            if len(buf) + len(sentence) + 1 > target_chars and buf:
                pieces.append(buf)
                buf = sentence
            else:
                buf = f"{buf} {sentence}".strip()
        if buf:
            pieces.append(buf)

    chunks: list[str] = []
    current: list[str] = []
    size = 0
    for piece in pieces:
        if current and size + len(piece) + 2 > target_chars:
            chunks.append("\n\n".join(current))
            tail = current[-1]
            current, size = ([tail], len(tail)) if overlap_chars and len(tail) <= overlap_chars else ([], 0)
        current.append(piece)
        size += len(piece) + 2
    if current:
        chunks.append("\n\n".join(current))
    return chunks

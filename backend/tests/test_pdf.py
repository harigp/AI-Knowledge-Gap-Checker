import pytest

from app.errors import FileTooLargeError, InvalidInputError
from app.services.pdf_service import chunk_text, estimate_tokens, extract_text
from tests.conftest import make_blank_pdf, make_encrypted_pdf, make_pdf, make_settings


def test_valid_pdf_extracts_text():
    doc = extract_text(make_pdf(pages=2), make_settings())
    assert doc.page_count == 2
    assert "least squares" in doc.text
    assert doc.estimated_tokens == estimate_tokens(doc.text)


def test_non_pdf_bytes_rejected():
    with pytest.raises(InvalidInputError) as e:
        extract_text(b"hello, I am a text file" * 50, make_settings())
    assert e.value.code == "invalid_file_type"


def test_corrupt_pdf_rejected():
    data = b"%PDF-1.7\n" + b"\x00garbage" * 200
    with pytest.raises(InvalidInputError) as e:
        extract_text(data, make_settings())
    assert e.value.code in {"invalid_pdf", "empty_pdf"}


def test_truncated_pdf_rejected():
    data = make_pdf()[:300]
    with pytest.raises(InvalidInputError) as e:
        extract_text(data, make_settings())
    assert e.value.code in {"invalid_pdf", "empty_pdf", "no_extractable_text"}


def test_empty_file_rejected():
    with pytest.raises(InvalidInputError) as e:
        extract_text(b"", make_settings())
    assert e.value.code == "empty_pdf"


def test_pdf_without_text_rejected():
    with pytest.raises(InvalidInputError) as e:
        extract_text(make_blank_pdf(pages=2), make_settings())
    assert e.value.code == "no_extractable_text"


def test_encrypted_pdf_rejected():
    with pytest.raises(InvalidInputError) as e:
        extract_text(make_encrypted_pdf(), make_settings())
    assert e.value.code == "encrypted_pdf"


def test_oversized_pdf_rejected():
    settings = make_settings(max_file_size_mb=0.001)  # ~1 KB
    with pytest.raises(FileTooLargeError):
        extract_text(make_pdf(), settings)


def test_too_many_pages_rejected():
    with pytest.raises(InvalidInputError) as e:
        extract_text(make_pdf(pages=4), make_settings(max_pages=3))
    assert e.value.code == "too_many_pages"
    assert e.value.details == {"max_pages": 3, "page_count": 4}


def test_chunking_respects_target_and_keeps_all_text():
    paragraphs = [f"Paragraph {i}. " + "word " * 300 for i in range(20)]
    text = "\n\n".join(paragraphs)
    chunks = chunk_text(text, target_tokens=1000, overlap_tokens=0)
    assert len(chunks) > 1
    assert all(len(c) <= 1000 * 4 for c in chunks)
    for i in range(20):
        assert any(f"Paragraph {i}." in c for c in chunks)


def test_chunking_splits_huge_paragraph():
    text = "This is a sentence. " * 2000  # one paragraph, ~40k chars
    chunks = chunk_text(text, target_tokens=1000, overlap_tokens=100)
    assert len(chunks) >= 10
    assert sum(len(c) for c in chunks) >= len(text.strip()) * 0.95

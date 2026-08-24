import pytest
from fastapi import HTTPException
from backend.app.services.parser import (
    clean_extracted_text, parse_pdf_file, parse_text_file, parse_resume_file
)

def test_clean_extracted_text():
    raw = "John Doe\n\n\n\u2022 Python Developer\x00"
    cleaned = clean_extracted_text(raw)
    assert "• Python Developer" in cleaned
    assert "\x00" not in cleaned

def test_parse_text_file():
    content = b"Candidate: Jane Doe\nSkills: Python, FastAPI"
    parsed = parse_text_file(content)
    assert "Jane Doe" in parsed
    assert "FastAPI" in parsed

def test_parse_pdf_file_valid():
    with open("samples/resumes/sarah_connor_devops.pdf", "rb") as f:
        pdf_bytes = f.read()
    parsed = parse_pdf_file(pdf_bytes)
    assert "Sarah Connor" in parsed
    assert "DevOps" in parsed

def test_parse_resume_file_unsupported():
    with pytest.raises(HTTPException) as exc_info:
        parse_resume_file("unsupported_file.docx", b"dummy content")
    assert exc_info.value.status_code == 400
    assert "Unsupported file format" in exc_info.value.detail

def test_parse_resume_file_empty():
    with pytest.raises(HTTPException) as exc_info:
        parse_resume_file("empty.txt", b"")
    assert exc_info.value.status_code == 400
    assert "Uploaded file is empty" in exc_info.value.detail

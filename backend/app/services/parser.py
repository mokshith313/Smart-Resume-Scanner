import io
import re
from pypdf import PdfReader
from fastapi import HTTPException

def clean_extracted_text(text: str) -> str:
    """Normalize extracted raw text by removing invalid characters and cleaning whitespace."""
    if not text:
        return ""
    # Normalize bullet points and dashes
    text = re.sub(r'[\u2022\u2023\u25e6\u2043\u2219]\s*', '• ', text)
    # Remove control characters except newlines/tabs
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', ' ', text)
    # Collapse multiple consecutive blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    # Clean whitespace per line
    lines = [line.strip() for line in text.splitlines()]
    return '\n'.join(lines).strip()


def parse_pdf_file(file_content: bytes) -> str:
    """Extract raw text from PDF byte content safely."""
    try:
        pdf_file = io.BytesIO(file_content)
        reader = PdfReader(pdf_file)
        
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception:
                raise ValueError("PDF is password protected and cannot be decrypted.")

        extracted_text_chunks = []
        for index, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text()
                if page_text:
                    extracted_text_chunks.append(page_text)
            except Exception as page_err:
                extracted_text_chunks.append(f"[Warning: Could not extract text from page {index+1}]")

        full_text = "\n\n".join(extracted_text_chunks)
        cleaned = clean_extracted_text(full_text)
        
        if not cleaned:
            return "[Note: PDF opened successfully but contained no extractable text. It may be an image-only PDF.]"
            
        return cleaned

    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Failed to parse PDF file: {str(e)}")


def parse_text_file(file_content: bytes) -> str:
    """Extract raw text from TXT byte content with encoding fallback."""
    encodings_to_try = ["utf-8", "latin-1", "ascii", "utf-16", "cp1252"]
    
    for encoding in encodings_to_try:
        try:
            raw_text = file_content.decode(encoding)
            cleaned = clean_extracted_text(raw_text)
            if cleaned:
                return cleaned
        except (UnicodeDecodeError, Exception):
            continue

    raise ValueError("Failed to decode text file. File may be binary or corrupt.")


def parse_resume_file(filename: str, file_content: bytes) -> tuple[str, str]:
    """
    Main entry point for resume parsing.
    Returns tuple of (parsed_text, file_type)
    """
    if not file_content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    filename_lower = filename.lower()
    
    if filename_lower.endswith(".pdf"):
        file_type = "pdf"
        parsed_text = parse_pdf_file(file_content)
    elif filename_lower.endswith(".txt"):
        file_type = "txt"
        parsed_text = parse_text_file(file_content)
    else:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format '{filename}'. Only PDF and TXT files are supported."
        )

    return parsed_text, file_type

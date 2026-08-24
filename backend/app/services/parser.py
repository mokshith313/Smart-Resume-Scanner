import pdfplumber

def parse_pdf_file(file_content: bytes) -> str:
    """Extract raw text from PDF byte content safely using pdfplumber with pypdf fallback."""
    extracted_text_chunks = []
    
    # 1. Primary Attempt: pdfplumber (Handles complex formatting & encodings best)
    try:
        pdf_file = io.BytesIO(file_content)
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    extracted_text_chunks.append(page_text)
    except Exception:
        extracted_text_chunks = []

    # 2. Fallback Attempt: pypdf (If pdfplumber returned no text)
    if not extracted_text_chunks:
        try:
            pdf_file = io.BytesIO(file_content)
            reader = PdfReader(pdf_file)
            
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception:
                    raise ValueError("PDF is password protected and cannot be decrypted.")

            for index, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text_chunks.append(page_text)
                except Exception:
                    continue
        except Exception as e:
            if isinstance(e, ValueError):
                raise
            raise ValueError(f"Failed to parse PDF file: {str(e)}")

    full_text = "\n\n".join(extracted_text_chunks)
    cleaned = clean_extracted_text(full_text)
    
    if not cleaned:
        return "[Note: PDF opened successfully but contained no extractable text. It may be an image-only PDF.]"
        
    return cleaned
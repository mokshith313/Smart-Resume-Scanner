from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.db.models import Resume
from backend.app.schemas.schemas import ResumeResponse
from backend.app.services.parser import parse_resume_file
from backend.app.services.extractor import extract_structured_resume_data, clean_name_from_filename

router = APIRouter(prefix="/resumes", tags=["Resumes"])

@router.post("/upload", response_model=list[ResumeResponse], status_code=status.HTTP_201_CREATED)
async def upload_resumes(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Batch upload candidate resumes (PDF or TXT formats).
    Parses raw text and extracts structured candidate data (skills, experience, education).
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    saved_resumes = []

    for file in files:
        filename = file.filename or "unknown_resume.pdf"
        try:
            content = await file.read()
            raw_text, file_type = parse_resume_file(filename, content)
            
            # Extract structured candidate data with filename fallback
            extracted = extract_structured_resume_data(raw_text, filename=filename)
            
            resume = Resume(
                filename=filename,
                file_type=file_type,
                raw_text=raw_text,
                candidate_name=extracted.candidate_name,
                email=extracted.contact_info.email if extracted.contact_info else None,
                extracted_data=extracted.model_dump(),
                extraction_status="success" if raw_text and not raw_text.startswith("[Note:") else "partial"
            )
            db.add(resume)
            saved_resumes.append(resume)

        except Exception as err:
            cand_name = clean_name_from_filename(filename)
            failed_resume = Resume(
                filename=filename,
                file_type="unknown",
                raw_text=f"[Error parsing file: {str(err)}]",
                candidate_name=cand_name,
                extracted_data=None,
                extraction_status="failed"
            )
            db.add(failed_resume)
            saved_resumes.append(failed_resume)

    db.commit()
    for r in saved_resumes:
        db.refresh(r)

    return saved_resumes


@router.get("/", response_model=list[ResumeResponse])
def list_resumes(db: Session = Depends(get_db)):
    """List all uploaded candidate resumes."""
    return db.query(Resume).order_by(Resume.uploaded_at.desc()).all()


@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume(resume_id: str, db: Session = Depends(get_db)):
    """Get details and extracted data for a single resume."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail=f"Resume with ID '{resume_id}' not found.")
    return resume


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(resume_id: str, db: Session = Depends(get_db)):
    """Delete a resume and its associated match results."""
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail=f"Resume with ID '{resume_id}' not found.")
    db.delete(resume)
    db.commit()
    return None

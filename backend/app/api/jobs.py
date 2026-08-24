from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.db.models import JobDescription
from backend.app.schemas.schemas import JobDescriptionCreate, JobDescriptionResponse
from backend.app.services.scorer import extract_skills_from_jd

router = APIRouter(prefix="/jobs", tags=["Job Descriptions"])

@router.post("/", response_model=JobDescriptionResponse, status_code=status.HTTP_201_CREATED)
def create_job_description(payload: JobDescriptionCreate, db: Session = Depends(get_db)):
    """Create and store a new Job Description."""
    if not payload.title.strip() or not payload.raw_text.strip():
        raise HTTPException(status_code=400, detail="Job title and raw text cannot be empty.")
    
    extracted_skills = extract_skills_from_jd(f"{payload.title}\n{payload.raw_text}")
    
    job = JobDescription(
        title=payload.title.strip(),
        company=payload.company.strip() if payload.company else "Target Company",
        raw_text=payload.raw_text.strip(),
        required_skills=extracted_skills
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

@router.get("/", response_model=list[JobDescriptionResponse])
def list_job_descriptions(db: Session = Depends(get_db)):
    """List all stored Job Descriptions."""
    return db.query(JobDescription).order_by(JobDescription.created_at.desc()).all()

@router.get("/{job_id}", response_model=JobDescriptionResponse)
def get_job_description(job_id: str, db: Session = Depends(get_db)):
    """Retrieve details for a specific Job Description."""
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job Description with ID '{job_id}' not found.")
    return job

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job_description(job_id: str, db: Session = Depends(get_db)):
    """Delete a Job Description and associated match results."""
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job Description with ID '{job_id}' not found.")
    db.delete(job)
    db.commit()
    return None

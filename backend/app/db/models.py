import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.db.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False)
    company = Column(String, nullable=True, default="Unknown Company")
    raw_text = Column(Text, nullable=False)
    required_skills = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    match_results = relationship("MatchResult", back_populates="job_description", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    raw_text = Column(Text, nullable=False)
    candidate_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    extracted_data = Column(JSON, nullable=True)
    extraction_status = Column(String, nullable=False, default="pending")
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    match_results = relationship("MatchResult", back_populates="resume", cascade="all, delete-orphan")


class MatchResult(Base):
    __tablename__ = "match_results"

    id = Column(String, primary_key=True, default=generate_uuid)
    resume_id = Column(String, ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    job_description_id = Column(String, ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=True)
    evaluation_mode = Column(String, nullable=False, default="role_match")  # role_match or general_quality
    overall_score = Column(Integer, nullable=False)  # 1-10 scale
    
    # Mode A (Role Match)
    matched_skills = Column(JSON, nullable=True, default=list)
    missing_critical_skills = Column(JSON, nullable=True, default=list)
    experience_fit_summary = Column(Text, nullable=True, default="")
    
    # Mode B (General Quality)
    top_strengths = Column(JSON, nullable=True, default=list)
    areas_for_improvement = Column(JSON, nullable=True, default=list)
    primary_domain = Column(String, nullable=True, default="General Profile")
    
    # Common Output
    justification = Column(Text, nullable=False)
    scored_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    resume = relationship("Resume", back_populates="match_results")
    job_description = relationship("JobDescription", back_populates="match_results")

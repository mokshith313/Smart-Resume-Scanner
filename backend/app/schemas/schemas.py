from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

# --- Resume Extraction Schemas ---

class ContactInfo(BaseModel):
    email: str | None = Field(default=None, description="Candidate email address")
    phone: str | None = Field(default=None, description="Candidate phone number")

class ExperienceItem(BaseModel):
    role: str = Field(default="Not specified", description="Job title or role")
    company: str = Field(default="Not specified", description="Company or organization name")
    duration: str = Field(default="Not specified", description="Dates or timeframe worked")
    responsibilities: str = Field(default="Not specified", description="Key duties and achievements")

class EducationItem(BaseModel):
    degree: str = Field(default="Not specified", description="Degree or certification earned")
    institution: str = Field(default="Not specified", description="University, college, or platform")
    year: str = Field(default="Not specified", description="Graduation year or dates")

class ExtractedResumeData(BaseModel):
    candidate_name: str = Field(default="Unknown Candidate", description="Full name of candidate")
    contact_info: ContactInfo = Field(default_factory=ContactInfo, description="Email and phone number")
    skills: list[str] = Field(default_factory=list, description="Extracted technical and soft skills")
    experience: list[ExperienceItem] = Field(default_factory=list, description="Work experience items")
    education: list[EducationItem] = Field(default_factory=list, description="Education background items")

# --- Dual-Mode LLM Match & Quality Evaluation Schema ---

class EvaluationResult(BaseModel):
    evaluation_mode: str = Field(default="role_match", description="'role_match' (Mode A) or 'general_quality' (Mode B)")
    overall_score: int = Field(..., ge=1, le=10, description="Overall fit or profile strength score on 1-10 scale")
    
    # Mode A Fields (Role Match against JD)
    matched_skills: list[str] = Field(default_factory=list, description="Skills matching JD requirements")
    missing_critical_skills: list[str] = Field(default_factory=list, description="Critical JD skills missing from resume")
    experience_fit_summary: str = Field(default="", description="Summary of work experience relevance to JD")
    
    # Mode B Fields (General Quality without JD)
    top_strengths: list[str] = Field(default_factory=list, description="Top candidate strengths and resume highlights")
    areas_for_improvement: list[str] = Field(default_factory=list, description="Key profile gaps or areas for improvement")
    primary_domain: str = Field(default="General Engineering", description="Inferred candidate specialization domain")
    
    # Common Output
    justification: str = Field(..., description="Evidence-grounded rationale referencing resume facts")

# --- Job Description Schemas ---

class JobDescriptionCreate(BaseModel):
    title: str = Field(..., description="Job title, e.g. Senior Backend Engineer")
    company: str | None = Field(default="Target Company", description="Hiring company name")
    raw_text: str = Field(..., description="Full text of the job description")

class JobDescriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    company: str | None
    raw_text: str
    required_skills: list[str] | None = None
    created_at: datetime

# --- Resume Schemas ---

class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    file_type: str
    candidate_name: str | None
    email: str | None
    extracted_data: ExtractedResumeData | None = None
    extraction_status: str
    uploaded_at: datetime

# --- Screening Request & Response Schemas ---

class ScreeningRequest(BaseModel):
    job_description_id: str | None = Field(default=None, description="Optional JD ID for Mode A. If None, runs Mode B General Evaluation.")
    resume_ids: list[str] | None = Field(default=None, description="Target resume IDs")

class MatchResultResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    resume_id: str
    job_description_id: str | None = None
    candidate_name: str
    candidate_email: str | None = None
    evaluation_mode: str = "role_match"
    overall_score: int
    matched_skills: list[str] = Field(default_factory=list)
    missing_critical_skills: list[str] = Field(default_factory=list)
    experience_fit_summary: str = ""
    top_strengths: list[str] = Field(default_factory=list)
    areas_for_improvement: list[str] = Field(default_factory=list)
    primary_domain: str = "General Profile"
    justification: str = ""
    extracted_data: ExtractedResumeData | None = None
    scored_at: datetime

class ShortlistResponse(BaseModel):
    job_id: str | None = None
    job_title: str
    company: str | None = None
    evaluation_mode: str = "role_match"
    total_screened: int
    candidates: list[MatchResultResponse]

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.db.models import JobDescription, Resume, MatchResult
from backend.app.schemas.schemas import (
    ScreeningRequest, ShortlistResponse, MatchResultResponse, ExtractedResumeData
)
from backend.app.services.scorer import score_resume_against_job

router = APIRouter(prefix="/screener", tags=["Smart Resume Screener"])

@router.post("/screen", response_model=ShortlistResponse, status_code=status.HTTP_200_OK)
def screen_resumes(payload: ScreeningRequest, db: Session = Depends(get_db)):
    """
    Trigger batch screening of resumes.
    - If job_description_id is provided -> Mode A (Role-Specific Match)
    - If job_description_id is None -> Mode B (General Profile Strength)
    """
    job = None
    job_title = "General Resume Evaluation"
    job_text = None
    evaluation_mode = "general_quality"

    if payload.job_description_id:
        job = db.query(JobDescription).filter(JobDescription.id == payload.job_description_id).first()
        if not job:
            raise HTTPException(status_code=404, detail=f"Job Description '{payload.job_description_id}' not found.")
        job_title = job.title
        job_text = job.raw_text
        evaluation_mode = "role_match"

    if payload.resume_ids:
        resumes = db.query(Resume).filter(Resume.id.in_(payload.resume_ids)).all()
    else:
        resumes = db.query(Resume).all()

    if not resumes:
        raise HTTPException(status_code=400, detail="No resumes available to screen.")

    screened_results = []

    for resume in resumes:
        job_id_filter = job.id if job else None
        
        existing_match = db.query(MatchResult).filter(
            MatchResult.resume_id == resume.id,
            MatchResult.job_description_id == job_id_filter
        ).first()

        extracted_obj = ExtractedResumeData(**(resume.extracted_data or {}))

        # Compute dual-mode evaluation result
        eval_res = score_resume_against_job(
            job_title=job_title if job else None,
            job_text=job_text,
            extracted_data=extracted_obj,
            raw_resume_text=resume.raw_text
        )

        if existing_match:
            existing_match.evaluation_mode = eval_res.evaluation_mode
            existing_match.overall_score = eval_res.overall_score
            existing_match.matched_skills = eval_res.matched_skills
            existing_match.missing_critical_skills = eval_res.missing_critical_skills
            existing_match.experience_fit_summary = eval_res.experience_fit_summary
            existing_match.top_strengths = eval_res.top_strengths
            existing_match.areas_for_improvement = eval_res.areas_for_improvement
            existing_match.primary_domain = eval_res.primary_domain
            existing_match.justification = eval_res.justification
            match_rec = existing_match
        else:
            match_rec = MatchResult(
                resume_id=resume.id,
                job_description_id=job.id if job else None,
                evaluation_mode=eval_res.evaluation_mode,
                overall_score=eval_res.overall_score,
                matched_skills=eval_res.matched_skills,
                missing_critical_skills=eval_res.missing_critical_skills,
                experience_fit_summary=eval_res.experience_fit_summary,
                top_strengths=eval_res.top_strengths,
                areas_for_improvement=eval_res.areas_for_improvement,
                primary_domain=eval_res.primary_domain,
                justification=eval_res.justification
            )
            db.add(match_rec)

        db.flush()

        screened_results.append(MatchResultResponse(
            id=match_rec.id,
            resume_id=resume.id,
            job_description_id=job.id if job else None,
            candidate_name=resume.candidate_name or "Unknown Candidate",
            candidate_email=resume.email,
            evaluation_mode=match_rec.evaluation_mode,
            overall_score=match_rec.overall_score,
            matched_skills=match_rec.matched_skills or [],
            missing_critical_skills=match_rec.missing_critical_skills or [],
            experience_fit_summary=match_rec.experience_fit_summary or "",
            top_strengths=match_rec.top_strengths or [],
            areas_for_improvement=match_rec.areas_for_improvement or [],
            primary_domain=match_rec.primary_domain or "General Profile",
            justification=match_rec.justification,
            extracted_data=extracted_obj,
            scored_at=match_rec.scored_at
        ))

    db.commit()

    screened_results.sort(key=lambda x: x.overall_score, reverse=True)

    return ShortlistResponse(
        job_id=job.id if job else None,
        job_title=job_title,
        company=job.company if job else "General Screening",
        evaluation_mode=evaluation_mode,
        total_screened=len(screened_results),
        candidates=screened_results
    )


@router.get("/shortlist/{job_id}", response_model=ShortlistResponse)
def get_ranked_shortlist(
    job_id: str,
    min_score: int | None = Query(default=None, ge=1, le=10, description="Filter candidates by minimum overall score"),
    search_query: str | None = Query(default=None, description="Search candidates by name or skill"),
    db: Session = Depends(get_db)
):
    """Retrieve ranked shortlist of candidates for a job description."""
    job = db.query(JobDescription).filter(JobDescription.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail=f"Job Description '{job_id}' not found.")

    query = db.query(MatchResult, Resume).join(Resume, MatchResult.resume_id == Resume.id).filter(
        MatchResult.job_description_id == job_id
    )

    if min_score is not None:
        query = query.filter(MatchResult.overall_score >= min_score)

    matches = query.order_by(MatchResult.overall_score.desc()).all()

    candidates_list = []
    for match_rec, resume_rec in matches:
        extracted_obj = ExtractedResumeData(**(resume_rec.extracted_data or {}))
        
        if search_query:
            sq = search_query.lower()
            name_match = sq in (resume_rec.candidate_name or "").lower()
            skill_match = any(sq in s.lower() for s in extracted_obj.skills)
            if not (name_match or skill_match):
                continue

        candidates_list.append(MatchResultResponse(
            id=match_rec.id,
            resume_id=resume_rec.id,
            job_description_id=job.id,
            candidate_name=resume_rec.candidate_name or "Unknown Candidate",
            candidate_email=resume_rec.email,
            evaluation_mode=match_rec.evaluation_mode,
            overall_score=match_rec.overall_score,
            matched_skills=match_rec.matched_skills or [],
            missing_critical_skills=match_rec.missing_critical_skills or [],
            experience_fit_summary=match_rec.experience_fit_summary or "",
            top_strengths=match_rec.top_strengths or [],
            areas_for_improvement=match_rec.areas_for_improvement or [],
            primary_domain=match_rec.primary_domain or "General Profile",
            justification=match_rec.justification,
            extracted_data=extracted_obj,
            scored_at=match_rec.scored_at
        ))

    return ShortlistResponse(
        job_id=job.id,
        job_title=job.title,
        company=job.company,
        evaluation_mode="role_match",
        total_screened=len(candidates_list),
        candidates=candidates_list
    )


@router.get("/match/{match_id}", response_model=MatchResultResponse)
def get_match_detail(match_id: str, db: Session = Depends(get_db)):
    """Fetch complete score breakdown and justification for a single candidate match."""
    match_tuple = db.query(MatchResult, Resume).join(Resume, MatchResult.resume_id == Resume.id).filter(
        MatchResult.id == match_id
    ).first()

    if not match_tuple:
        raise HTTPException(status_code=404, detail=f"Match Result '{match_id}' not found.")

    match_rec, resume_rec = match_tuple
    extracted_obj = ExtractedResumeData(**(resume_rec.extracted_data or {}))

    return MatchResultResponse(
        id=match_rec.id,
        resume_id=resume_rec.id,
        job_description_id=match_rec.job_description_id,
        candidate_name=resume_rec.candidate_name or "Unknown Candidate",
        candidate_email=resume_rec.email,
        evaluation_mode=match_rec.evaluation_mode,
        overall_score=match_rec.overall_score,
        matched_skills=match_rec.matched_skills or [],
        missing_critical_skills=match_rec.missing_critical_skills or [],
        experience_fit_summary=match_rec.experience_fit_summary or "",
        top_strengths=match_rec.top_strengths or [],
        areas_for_improvement=match_rec.areas_for_improvement or [],
        primary_domain=match_rec.primary_domain or "General Profile",
        justification=match_rec.justification,
        extracted_data=extracted_obj,
        scored_at=match_rec.scored_at
    )

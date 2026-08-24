import re
from backend.app.schemas.schemas import ExtractedResumeData, EvaluationResult
from backend.app.services.llm import execute_llm_json_prompt

# --- MODE A PROMPTS (With Job Description) ---

SCORING_MODE_A_SYSTEM_PROMPT = """You are a senior technical recruiter and talent evaluator. Compare candidate resumes against job requirements and produce objective, evidence-grounded fit scores (1-10) with detailed justifications."""

SCORING_MODE_A_USER_PROMPT = """Compare the candidate's structured resume against the target job description. Evaluate technical fit, experience depth, and missing qualifications.

JOB DESCRIPTION:
================
Title: {job_title}
Text:
{job_text}
================

CANDIDATE RESUME PROFILE:
=========================
Candidate Name: {candidate_name}
Extracted Skills: {skills}
Work Experience:
{experience_summary}

Education:
{education_summary}

Raw Resume Snippet:
{resume_snippet}
=========================

INSTRUCTIONS:
Rate candidate fit on an integer scale from 1 to 10.
Return ONLY a JSON object matching this schema:
{{
  "evaluation_mode": "role_match",
  "overall_score": 8,
  "matched_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
  "missing_critical_skills": ["Kubernetes", "AWS"],
  "experience_fit_summary": "5+ years of relevant experience building Python microservices.",
  "justification": "Candidate demonstrates strong fit for the Senior Backend Engineer role due to..."
}}
"""

# --- MODE B PROMPTS (Without Job Description) ---

SCORING_MODE_B_SYSTEM_PROMPT = """You are an expert executive recruiter and resume reviewer. Evaluate candidate profile strength, skill density, career progression, and educational background without a target job description."""

SCORING_MODE_B_USER_PROMPT = """Evaluate general candidate resume profile strength, skill density, career progression, and presentation quality without a target job description.

CANDIDATE RESUME PROFILE:
=========================
Candidate Name: {candidate_name}
Extracted Skills: {skills}
Work Experience:
{experience_summary}

Education:
{education_summary}

Raw Resume Snippet:
{resume_snippet}
=========================

INSTRUCTIONS:
Compute a 1-10 General Profile Strength Score evaluating overall resume impact, career progression clarity, technical/soft skill density, formatting quality, and education.
Return ONLY a JSON object matching this schema:
{{
  "evaluation_mode": "general_quality",
  "overall_score": 8,
  "top_strengths": [
    "High technical skill density with verified proficiency in backend systems",
    "Clear career progression across senior engineering roles",
    "Strong educational background from a reputable institution"
  ],
  "areas_for_improvement": [
    "Quantify key achievements with measurable impact metrics (e.g. % performance increase)",
    "Add explicit certifications or cloud platform badges"
  ],
  "primary_domain": "Backend Software Engineering",
  "justification": "Candidate presents a well-structured, high-impact resume with 5+ years of software development experience..."
}}
"""


def extract_skills_from_jd(job_text: str) -> list[str]:
    """Extract required skills and keywords from Job Description text."""
    from backend.app.services.extractor import KNOWN_SKILLS
    found = []
    for skill in KNOWN_SKILLS:
        if re.search(r'\b' + re.escape(skill) + r'\b', job_text, re.IGNORECASE):
            found.append(skill)
    return found


def infer_primary_domain(skills: list[str], raw_text: str) -> str:
    """Infer candidate primary domain tag from skills and resume content."""
    text = (raw_text + " " + " ".join(skills)).lower()
    if any(k in text for k in ["data science", "pytorch", "tensorflow", "machine learning", "nlp", "pandas"]):
        return "Data Science & Machine Learning"
    elif any(k in text for k in ["devops", "kubernetes", "docker", "terraform", "aws", "ci/cd"]):
        return "DevOps & Cloud Engineering"
    elif any(k in text for k in ["frontend", "react", "vue", "javascript", "css", "html", "ui/ux"]):
        return "Frontend Web Development"
    elif any(k in text for k in ["fastapi", "django", "flask", "python", "postgresql", "backend", "microservices"]):
        return "Backend Software Engineering"
    return "Full Stack Software Engineering"


# --- FALLBACK SCORING ENGINES ---

def fallback_mode_a_scorer(
    job_title: str,
    job_text: str,
    extracted_data: ExtractedResumeData,
    raw_resume_text: str
) -> EvaluationResult:
    """Fallback scorer for Mode A (With Job Description)."""
    candidate_name = extracted_data.candidate_name or "Candidate"
    
    jd_skills = extract_skills_from_jd(f"{job_title}\n{job_text}")
    candidate_skills = extracted_data.skills or []
    
    raw_lower = raw_resume_text.lower()
    candidate_skills_set = set(s.lower() for s in candidate_skills)
    
    matched_skills = []
    missing_critical_skills = []
    
    if jd_skills:
        for skill in jd_skills:
            if skill.lower() in candidate_skills_set or re.search(r'\b' + re.escape(skill.lower()) + r'\b', raw_lower):
                matched_skills.append(skill)
            else:
                missing_critical_skills.append(skill)
        skill_score_ratio = len(matched_skills) / len(jd_skills)
    else:
        skill_score_ratio = 0.6
        matched_skills = candidate_skills[:5]

    job_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', job_text.lower()))
    resume_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', raw_lower))
    
    common_words = job_words.intersection(resume_words)
    keyword_overlap = len(common_words) / max(1, len(job_words))

    base_score = 1.0 + (skill_score_ratio * 6.0) + (keyword_overlap * 3.0)
    
    exp_text = " ".join([f"{e.role} {e.company} {e.responsibilities}" for e in extracted_data.experience])
    if any(k in exp_text.lower() for k in ["senior", "lead", "architect", "5+", "manager"]):
        base_score += 0.5
        
    overall_score = int(round(min(10.0, max(1.0, base_score))))

    matched_str = ", ".join(matched_skills) if matched_skills else "general engineering principles"
    missing_str = ", ".join(missing_critical_skills) if missing_critical_skills else "none identified"
    
    experience_fit_summary = f"Evaluated {len(extracted_data.experience)} experience record(s). Demonstrates practical alignment matching core job requirements."

    justification = (
        f"{candidate_name} achieved an overall role fit score of {overall_score}/10 for '{job_title}'. "
        f"Verified alignment in key required technical domains including: {matched_str}. "
    )
    if missing_critical_skills:
        justification += f"However, potential gaps were noted in: {missing_str}. "
    else:
        justification += "Covers all explicitly requested technical competencies in the job description. "

    return EvaluationResult(
        evaluation_mode="role_match",
        overall_score=overall_score,
        matched_skills=matched_skills,
        missing_critical_skills=missing_critical_skills,
        experience_fit_summary=experience_fit_summary,
        justification=justification
    )


def fallback_mode_b_scorer(
    extracted_data: ExtractedResumeData,
    raw_resume_text: str
) -> EvaluationResult:
    """Fallback scorer for Mode B (General Profile Strength without Job Description)."""
    candidate_name = extracted_data.candidate_name or "Candidate"
    skills = extracted_data.skills or []
    experience = extracted_data.experience or []
    education = extracted_data.education or []
    
    domain = infer_primary_domain(skills, raw_resume_text)

    # Base score heuristics: skill density (3 pts), experience depth (4 pts), education (2 pts), formatting (1 pt)
    skill_score = min(3.0, len(skills) * 0.5)
    exp_score = min(4.0, len(experience) * 1.5)
    edu_score = 2.0 if education and education[0].degree != "Not specified" else 1.0
    format_score = 1.0 if len(raw_resume_text) > 200 else 0.5
    
    overall_score = int(round(min(10.0, max(1.0, skill_score + exp_score + edu_score + format_score))))

    top_strengths = []
    if skills:
        top_strengths.append(f"Strong skill density across: {', '.join(skills[:5])}")
    if experience:
        top_strengths.append(f"Recorded {len(experience)} professional work history entry/entries")
    if education and education[0].degree != "Not specified":
        top_strengths.append(f"Formal education background: {education[0].degree}")
    if not top_strengths:
        top_strengths.append("Contains baseline resume structure")

    areas_for_improvement = [
        "Include quantitative metrics & business impact metrics for key projects",
        "Highlight cloud or modern framework certifications"
    ]

    justification = (
        f"{candidate_name} scored a General Profile Strength of {overall_score}/10 in the domain of '{domain}'. "
        f"The candidate demonstrates solid career background with {len(skills)} identified technical/soft skills and "
        f"{len(experience)} documented professional experience position(s)."
    )

    return EvaluationResult(
        evaluation_mode="general_quality",
        overall_score=overall_score,
        top_strengths=top_strengths,
        areas_for_improvement=areas_for_improvement,
        primary_domain=domain,
        justification=justification
    )


# --- MAIN SCORING ENTRY POINT ---

def score_resume_against_job(
    job_title: str | None,
    job_text: str | None,
    extracted_data: ExtractedResumeData,
    raw_resume_text: str
) -> EvaluationResult:
    """
    Main match & scoring entry point.
    - If job_text is provided -> Mode A (Role-Specific Match)
    - If job_text is None/empty -> Mode B (General Profile Strength)
    """
    candidate_name = extracted_data.candidate_name or "Unknown Candidate"
    skills_str = ", ".join(extracted_data.skills) if extracted_data.skills else "None listed"
    
    exp_summary = "\n".join([
        f"- {e.role} at {e.company} ({e.duration}): {e.responsibilities}" 
        for e in extracted_data.experience
    ]) or "No explicit work experience section."
    
    edu_summary = "\n".join([
        f"- {e.degree} at {e.institution} ({e.year})"
        for e in extracted_data.education
    ]) or "No explicit education section."

    # --- MODE A: Role-Specific Match ---
    if job_title and job_text and len(job_text.strip()) > 0:
        prompt = SCORING_MODE_A_USER_PROMPT.format(
            job_title=job_title,
            job_text=job_text[:3000],
            candidate_name=candidate_name,
            skills=skills_str,
            experience_summary=exp_summary[:1500],
            education_summary=edu_summary[:800],
            resume_snippet=raw_resume_text[:1500]
        )

        llm_res = execute_llm_json_prompt(prompt, SCORING_MODE_A_SYSTEM_PROMPT)

        if llm_res and isinstance(llm_res, dict) and "overall_score" in llm_res and "justification" in llm_res:
            try:
                score = int(round(float(llm_res["overall_score"])))
                score = min(10, max(1, score))
                
                return EvaluationResult(
                    evaluation_mode="role_match",
                    overall_score=score,
                    matched_skills=list(llm_res.get("matched_skills", [])),
                    missing_critical_skills=list(llm_res.get("missing_critical_skills", [])),
                    experience_fit_summary=str(llm_res.get("experience_fit_summary", "")),
                    justification=str(llm_res.get("justification", ""))
                )
            except Exception:
                pass

        return fallback_mode_a_scorer(job_title, job_text, extracted_data, raw_resume_text)

    # --- MODE B: General Resume Quality ---
    else:
        prompt = SCORING_MODE_B_USER_PROMPT.format(
            candidate_name=candidate_name,
            skills=skills_str,
            experience_summary=exp_summary[:1500],
            education_summary=edu_summary[:800],
            resume_snippet=raw_resume_text[:1500]
        )

        llm_res = execute_llm_json_prompt(prompt, SCORING_MODE_B_SYSTEM_PROMPT)

        if llm_res and isinstance(llm_res, dict) and "overall_score" in llm_res and "justification" in llm_res:
            try:
                score = int(round(float(llm_res["overall_score"])))
                score = min(10, max(1, score))
                
                return EvaluationResult(
                    evaluation_mode="general_quality",
                    overall_score=score,
                    top_strengths=list(llm_res.get("top_strengths", [])),
                    areas_for_improvement=list(llm_res.get("areas_for_improvement", [])),
                    primary_domain=str(llm_res.get("primary_domain", "General Profile")),
                    justification=str(llm_res.get("justification", ""))
                )
            except Exception:
                pass

        return fallback_mode_b_scorer(extracted_data, raw_resume_text)

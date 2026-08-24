from backend.app.schemas.schemas import ExtractedResumeData, ContactInfo, ExperienceItem, EducationItem
from backend.app.services.scorer import score_resume_against_job, fallback_mode_a_scorer, fallback_mode_b_scorer

def test_semantic_scorer_mode_a_strong_match():
    job_title = "Senior Backend Engineer"
    job_text = "Looking for a Senior Backend Engineer with Python, FastAPI, PostgreSQL, and Docker."

    extracted = ExtractedResumeData(
        candidate_name="John Doe",
        contact_info=ContactInfo(email="john@example.com"),
        skills=["Python", "FastAPI", "PostgreSQL", "Docker", "Git"],
        experience=[
            ExperienceItem(role="Senior Developer", company="TechCorp", duration="2021-2024", responsibilities="Built Python microservices")
        ],
        education=[
            EducationItem(degree="B.S. Computer Science", institution="MIT", year="2021")
        ]
    )
    raw_text = "John Doe Python FastAPI PostgreSQL Docker Git"

    result = score_resume_against_job(job_title, job_text, extracted, raw_text)
    assert result.evaluation_mode == "role_match"
    assert 1 <= result.overall_score <= 10
    assert result.overall_score >= 8
    assert len(result.justification) > 20
    assert "Python" in result.matched_skills

def test_semantic_scorer_mode_b_general_quality():
    extracted = ExtractedResumeData(
        candidate_name="Sarah Connor",
        contact_info=ContactInfo(email="sarah@devops.net"),
        skills=["Docker", "Kubernetes", "AWS", "Python", "CI/CD"],
        experience=[
            ExperienceItem(role="DevOps Specialist", company="Cyberdyne", duration="2020-2024", responsibilities="Managed K8s clusters")
        ],
        education=[
            EducationItem(degree="B.S. IT", institution="MIT", year="2020")
        ]
    )
    raw_text = "Sarah Connor DevOps Specialist Docker Kubernetes AWS Python CI/CD"

    result = score_resume_against_job(None, None, extracted, raw_text)
    assert result.evaluation_mode == "general_quality"
    assert 1 <= result.overall_score <= 10
    assert len(result.top_strengths) > 0
    assert result.primary_domain is not None

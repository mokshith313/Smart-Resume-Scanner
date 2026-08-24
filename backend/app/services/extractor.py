import re
from backend.app.schemas.schemas import ExtractedResumeData, ContactInfo, ExperienceItem, EducationItem
from backend.app.services.llm import execute_llm_json_prompt

EXTRACTION_SYSTEM_PROMPT = """You are an expert ATS data extraction system. Extract accurate structured information from resume text into a strict JSON output format."""

EXTRACTION_USER_PROMPT = """Analyze the following resume text and extract candidate information into JSON format.

Return ONLY a JSON object with this exact structure:
{{
  "candidate_name": "Candidate's full name",
  "contact_info": {{
    "email": "candidate email address or null",
    "phone": "candidate phone number or null"
  }},
  "skills": ["Skill 1", "Skill 2", "Skill 3"],
  "experience": [
    {{
      "role": "Job title",
      "company": "Company name",
      "duration": "Dates/Timeframe e.g. 2020 - 2023",
      "responsibilities": "Summary of responsibilities and achievements"
    }}
  ],
  "education": [
    {{
      "degree": "Degree title or certification",
      "institution": "University/College/Organization",
      "year": "Year or dates"
    }}
  ]
}}

Resume Text:
----------------
{resume_text}
----------------
"""

KNOWN_SKILLS = [
    "Python", "Java", "C++", "C#", "JavaScript", "TypeScript", "Go", "Rust", "Ruby", "PHP", "Swift", "Kotlin",
    "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch", "Cassandra", "DynamoDB", "SQLite",
    "FastAPI", "Flask", "Django", "Node.js", "Express", "React", "Next.js", "Vue.js", "Angular", "Spring Boot",
    "Docker", "Kubernetes", "AWS", "GCP", "Azure", "Terraform", "CI/CD", "Git", "GitHub", "Jenkins", "Linux",
    "Machine Learning", "Deep Learning", "NLP", "PyTorch", "TensorFlow", "Pandas", "NumPy", "Scikit-Learn",
    "REST API", "GraphQL", "gRPC", "Microservices", "System Design", "Agile", "Scrum", "Jira", "Unit Testing",
    "HTML", "HTML5", "CSS", "CSS3", "Figma", "Photoshop", "UI/UX",
    "Communication", "Leadership", "Problem Solving", "Teamwork", "Project Management", "Data Analysis"
]


def fallback_rule_based_extractor(resume_text: str) -> ExtractedResumeData:
    """Fallback rule-based & regex parser when LLM is unavailable or fails."""
    # 1. Extract Contact Info
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', resume_text)
    phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', resume_text)
    
    email = email_match.group(0) if email_match else None
    phone = phone_match.group(0) if phone_match else None
    contact_info = ContactInfo(email=email, phone=phone)

    # 2. Extract Candidate Name
    candidate_name = "Unknown Candidate"
    lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
    if lines:
        for line in lines[:5]:
            if not re.search(r'@|\d{7,}|resume|curriculum|page', line, re.IGNORECASE) and len(line.split()) <= 4:
                candidate_name = line.strip()
                break

    # 3. Extract Skills
    found_skills = set()
    for skill in KNOWN_SKILLS:
        if re.search(r'\b' + re.escape(skill) + r'\b', resume_text, re.IGNORECASE):
            found_skills.add(skill)

    # 4. Extract Experience items
    experience_list = []
    exp_section = re.search(r'(?i)(?:work|professional)\s+experience\s*[:\n](.*?)(?=\n\n[A-Z\s]{4,}:|education|$)', resume_text, re.DOTALL)
    if exp_section:
        exp_text = exp_section.group(1).strip()
        blocks = re.split(r'\n(?=[A-Z0-9][a-zA-B0-9\s,|-]{3,30}\s*\(?\d{4})', exp_text)
        for block in blocks[:4]:
            block_lines = [l.strip() for l in block.splitlines() if l.strip()]
            if block_lines:
                role_company = block_lines[0]
                duration_match = re.search(r'(\d{4}|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\d{4}\b)\s*[-–to]+\s*(\d{4}|Present|Current|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s*\d{4}\b)', block, re.IGNORECASE)
                duration = duration_match.group(0) if duration_match else "Not specified"
                resp = " ".join(block_lines[1:]) if len(block_lines) > 1 else block_lines[0]
                experience_list.append(ExperienceItem(
                    role=role_company[:50],
                    company="Extracted Experience",
                    duration=duration,
                    responsibilities=resp[:250]
                ))

    if not experience_list:
        experience_list.append(ExperienceItem(
            role="Professional",
            company="Relevant Industry Experience",
            duration="Extracted from Resume",
            responsibilities=resume_text[:200]
        ))

    # 5. Extract Education items
    education_list = []
    edu_section = re.search(r'(?i)education\s*[:\n](.*?)(?=\n\n[A-Z\s]{4,}:|skills|experience|$)', resume_text, re.DOTALL)
    if edu_section:
        edu_text = edu_section.group(1).strip()
        edu_lines = [l.strip() for l in edu_text.splitlines() if l.strip()]
        if edu_lines:
            year_match = re.search(r'\b(19|20)\d{2}\b', edu_text)
            education_list.append(EducationItem(
                degree=edu_lines[0][:60],
                institution=edu_lines[1][:60] if len(edu_lines) > 1 else "University / Institution",
                year=year_match.group(0) if year_match else "Not specified"
            ))

    if not education_list:
        degree_match = re.search(r'(?i)\b(bachelor|master|phd|b\.s\.|m\.s\.|b\.tech|m\.tech|b\.a\.|m\.a\.)\b.*', resume_text)
        if degree_match:
            education_list.append(EducationItem(
                degree=degree_match.group(0)[:60],
                institution="University",
                year="Not specified"
            ))
        else:
            education_list.append(EducationItem(
                degree="Degree / Certification",
                institution="Educational Institution",
                year="Not specified"
            ))

    return ExtractedResumeData(
        candidate_name=candidate_name,
        contact_info=contact_info,
        skills=sorted(list(found_skills)),
        experience=experience_list,
        education=education_list
    )


def extract_structured_resume_data(resume_text: str) -> ExtractedResumeData:
    """Main extraction pipeline combining LLM JSON parsing with robust rule fallback."""
    if not resume_text or len(resume_text.strip()) == 0:
        return ExtractedResumeData(candidate_name="Empty Resume")

    prompt = EXTRACTION_USER_PROMPT.format(resume_text=resume_text[:4000])
    llm_dict = execute_llm_json_prompt(prompt, EXTRACTION_SYSTEM_PROMPT)

    if llm_dict:
        try:
            ci_raw = llm_dict.get("contact_info", {})
            contact = ContactInfo(
                email=ci_raw.get("email") if isinstance(ci_raw, dict) else None,
                phone=ci_raw.get("phone") if isinstance(ci_raw, dict) else None
            )

            skills = llm_dict.get("skills", [])
            if isinstance(skills, str):
                skills = [s.strip() for s in skills.split(",")]
            
            exp_raw = llm_dict.get("experience", [])
            experience_items = []
            if isinstance(exp_raw, list):
                for item in exp_raw:
                    if isinstance(item, dict):
                        experience_items.append(ExperienceItem(
                            role=str(item.get("role", "Not specified")),
                            company=str(item.get("company", "Not specified")),
                            duration=str(item.get("duration", "Not specified")),
                            responsibilities=str(item.get("responsibilities", "Not specified"))
                        ))

            edu_raw = llm_dict.get("education", [])
            education_items = []
            if isinstance(edu_raw, list):
                for item in edu_raw:
                    if isinstance(item, dict):
                        education_items.append(EducationItem(
                            degree=str(item.get("degree", "Not specified")),
                            institution=str(item.get("institution", "Not specified")),
                            year=str(item.get("year", "Not specified"))
                        ))

            return ExtractedResumeData(
                candidate_name=str(llm_dict.get("candidate_name", "Unknown Candidate")),
                contact_info=contact,
                skills=[str(s) for s in skills if s],
                experience=experience_items,
                education=education_items
            )
        except Exception:
            pass

    return fallback_rule_based_extractor(resume_text)

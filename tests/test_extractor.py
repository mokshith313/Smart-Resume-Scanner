from backend.app.services.extractor import extract_structured_resume_data, fallback_rule_based_extractor

def test_fallback_rule_based_extractor():
    sample_text = """John Doe
Email: john.doe@example.com

PROFESSIONAL SUMMARY
Experienced Software Engineer proficient in Python, FastAPI, and PostgreSQL.

WORK EXPERIENCE
Senior Developer | TechCorp (2021 - 2023)
- Led backend engineering team building Python REST APIs.

EDUCATION
B.S. Computer Science | MIT (2021)
"""
    extracted = fallback_rule_based_extractor(sample_text)
    assert extracted.candidate_name == "John Doe"
    assert extracted.contact_info.email == "john.doe@example.com"
    assert "Python" in extracted.skills
    assert "FastAPI" in extracted.skills
    assert "PostgreSQL" in extracted.skills
    assert len(extracted.experience) > 0
    assert len(extracted.education) > 0

def test_extract_structured_resume_data_empty():
    extracted = extract_structured_resume_data("")
    assert extracted.candidate_name == "Empty Resume"

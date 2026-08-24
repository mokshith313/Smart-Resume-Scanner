"""
Benchmark Evaluation Script for Smart Resume Screener (eval.py)
Evaluates Extraction Accuracy, Dual Scoring Modes (Mode A & Mode B), and Scoring Consistency.
"""

from backend.app.services.extractor import extract_structured_resume_data
from backend.app.services.scorer import score_resume_against_job

BENCHMARK_CASES = [
    {
        "id": "tc1_backend_senior",
        "raw_text": """John Doe
Email: john.doe@techcorp.io
Phone: (555) 019-2831

SUMMARY
Senior Backend Engineer with 5+ years of experience in Python, FastAPI, PostgreSQL, Docker, and AWS.

WORK EXPERIENCE
Senior Backend Engineer | TechCorp Inc (2021 - 2024)
- Architected Python FastAPI microservices serving millions of requests.
- Optimized PostgreSQL database schema and queries.

EDUCATION
B.S. in Computer Science | Stanford University (2021)
""",
        "expected_name": "John Doe",
        "expected_email": "john.doe@techcorp.io",
        "expected_skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        "job_title": "Senior Backend Engineer",
        "job_text": "Required Skills: Python, FastAPI, PostgreSQL, Docker, AWS. Experience building microservices.",
        "expected_min_score": 8
    },
    {
        "id": "tc2_frontend_weak",
        "raw_text": """Alice UI
Email: alice@designhub.org

SUMMARY
Frontend Developer specializing in React, CSS, and HTML.

WORK EXPERIENCE
UI Developer | DesignHub (2022 - 2024)
- Designed responsive interfaces using React.

EDUCATION
B.A. Graphic Design | NYU (2022)
""",
        "expected_name": "Alice UI",
        "expected_email": "alice@designhub.org",
        "expected_skills": ["React", "CSS", "HTML"],
        "job_title": "Senior Backend Engineer",
        "job_text": "Required Skills: Python, FastAPI, PostgreSQL, Docker, AWS. Experience building microservices.",
        "expected_max_score": 5
    }
]


def evaluate_extraction_accuracy():
    print("\n--- 1. Evaluating Extraction Accuracy ---")
    total_fields = 0
    correct_fields = 0

    for test in BENCHMARK_CASES:
        extracted = extract_structured_resume_data(test["raw_text"])
        
        # Check Name
        total_fields += 1
        if test["expected_name"].lower() in extracted.candidate_name.lower():
            correct_fields += 1
            print(f"  [PASS] Candidate Name: {extracted.candidate_name}")
        else:
            print(f"  [FAIL] Candidate Name: Got '{extracted.candidate_name}', expected '{test['expected_name']}'")

        # Check Email
        total_fields += 1
        extracted_email = extracted.contact_info.email if extracted.contact_info else None
        if extracted_email and extracted_email.lower() == test["expected_email"].lower():
            correct_fields += 1
            print(f"  [PASS] Email: {extracted_email}")
        else:
            print(f"  [FAIL] Email: Got '{extracted_email}', expected '{test['expected_email']}'")

        # Check Skill Extraction Overlap
        total_fields += 1
        extracted_skills_lower = set(s.lower() for s in extracted.skills)
        expected_skills_lower = set(s.lower() for s in test["expected_skills"])
        matched = expected_skills_lower.intersection(extracted_skills_lower)
        skill_acc = len(matched) / len(expected_skills_lower)
        
        if skill_acc >= 0.75:
            correct_fields += 1
            print(f"  [PASS] Skill Extraction Accuracy: {round(skill_acc * 100, 1)}% ({len(matched)}/{len(expected_skills_lower)} matched)")
        else:
            print(f"  [FAIL] Skill Extraction Accuracy: {round(skill_acc * 100, 1)}% below threshold")

    overall_accuracy = (correct_fields / total_fields) * 100
    print(f"\nOverall Extraction Accuracy: {overall_accuracy:.1f}% (Target: ≥85%)")
    assert overall_accuracy >= 85.0, "Extraction accuracy below target threshold!"


def evaluate_dual_scoring_modes():
    print("\n--- 2. Evaluating Dual Scoring Modes (Mode A vs Mode B) ---")
    
    test_resume = BENCHMARK_CASES[0]
    extracted = extract_structured_resume_data(test_resume["raw_text"])

    # Mode A: Role Specific
    res_mode_a = score_resume_against_job(
        job_title=test_resume["job_title"],
        job_text=test_resume["job_text"],
        extracted_data=extracted,
        raw_resume_text=test_resume["raw_text"]
    )
    print(f"  [Mode A - With JD]: Mode={res_mode_a.evaluation_mode} | Score={res_mode_a.overall_score}/10 | Matched={len(res_mode_a.matched_skills)}")
    assert res_mode_a.evaluation_mode == "role_match"
    assert len(res_mode_a.matched_skills) > 0

    # Mode B: General Quality
    res_mode_b = score_resume_against_job(
        job_title=None,
        job_text=None,
        extracted_data=extracted,
        raw_resume_text=test_resume["raw_text"]
    )
    print(f"  [Mode B - Without JD]: Mode={res_mode_b.evaluation_mode} | Score={res_mode_b.overall_score}/10 | Domain={res_mode_b.primary_domain}")
    assert res_mode_b.evaluation_mode == "general_quality"
    assert len(res_mode_b.top_strengths) > 0

    print("Dual Scoring Modes Verification PASSED!")


def evaluate_scoring_consistency():
    print("\n--- 3. Evaluating Scoring Consistency (Stability Test) ---")
    iterations = 3
    
    for test in BENCHMARK_CASES:
        extracted = extract_structured_resume_data(test["raw_text"])
        scores = []
        
        for i in range(iterations):
            eval_res = score_resume_against_job(
                job_title=test["job_title"],
                job_text=test["job_text"],
                extracted_data=extracted,
                raw_resume_text=test["raw_text"]
            )
            scores.append(eval_res.overall_score)

        score_range = max(scores) - min(scores)
        avg_score = sum(scores) / len(scores)
        print(f"  TestCase [{test['id']}]: Iteration Scores = {scores} | Range = ±{score_range:.1f} pts")
        
        assert score_range <= 1.0, f"Scoring instability detected! Range {score_range} > 1.0"

    print("Scoring Consistency Check PASSED! Score stability within ±1 point requirement.")


def run_benchmark():
    print("=====================================================")
    print(" SMART RESUME SCREENER - BENCHMARK EVALUATION (eval.py)")
    print("=====================================================")
    
    evaluate_extraction_accuracy()
    evaluate_dual_scoring_modes()
    evaluate_scoring_consistency()
    
    print("\n🎉 ALL EVALUATION BENCHMARKS PASSED SUCCESSFULY!")

if __name__ == "__main__":
    run_benchmark()

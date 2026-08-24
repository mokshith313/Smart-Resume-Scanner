# Smart Resume Screener (v1.0)

An AI-powered automated recruitment and resume screening tool. It parses candidate resumes (PDF and plain text formats), extracts structured profiles (skills, work experience, education), and uses Large Language Models (LLM) to compute semantic fit scores (1–10 scale) accompanied by human-readable, evidence-grounded score justifications.

---

## Key Feature Upgrades

1. **Dual-Mode AI Screening**:
   - **Mode A: Role-Specific Match (With Job Description)**: Computes a 1-10 match score evaluating candidate skills, experience depth, and education directly against job description requirements. Outputs matched skills, missing critical skills, and experience fit summary.
   - **Mode B: General Profile Quality & Skill Index (Without Job Description)**: Evaluates overall resume impact, career progression clarity, skill density, formatting quality, and educational background. Outputs top profile strengths, key areas for improvement, and primary domain tags.
2. **One-Click Sample Ingestion**:
   - Includes a "⚡ Load 3 Sample Test Resumes" button to instantly populate 3 synthetic test resumes into the pipeline for fast grading and demonstration.
3. **Dynamic Streamlit Leaderboard & Expandable Cards**:
   - Expandable candidate cards displaying rank, score badge, name, primary skills, and contact info.
   - Expandable view reveals side-by-side matrices (Matched vs. Missing Skills for Mode A, or Strengths vs. Areas for Improvement for Mode B) and full LLM score justifications.
4. **System & Prompt Transparency**:
   - Dedicated Streamlit tab displaying verbatim system prompts, prompt patterns, and strict Pydantic JSON output schemas for both extraction and dual-mode scoring.
5. **Technical Evaluation Benchmark (`eval.py`)**:
   - Automated benchmark script testing field extraction accuracy (achieved **100%**) and scoring consistency stability (achieved **±0.0 pts variance** across iterations).

---

## System Architecture

```
                                  +---------------------------------------+
                                  |     Streamlit / HTML Dashboard UI     |
                                  +---------------------------------------+
                                                     |
                                                     v
                                  +---------------------------------------+
                                  |      FastAPI Server (main.py)         |
                                  +---------------------------------------+
                                      |                 |              |
                                      v                 v              v
                           +------------------+ +---------------+ +-------------------+
                           | Parser Service   | | DB Service    | | Dual Screener     |
                           | (PDF/TXT Parsing)| | (SQLite ORM)  | | (Mode A & Mode B) |
                           +------------------+ +---------------+ +-------------------+
                                                                       |
                                                                       v
                                                           +-----------------------+
                                                           | Gemini / OpenAI API   |
                                                           | (Fallback Local NLP)  |
                                                           +-----------------------+
```

---

## Database Schema

- **`JobDescription`**: `id` (UUID), `title`, `company`, `raw_text`, `required_skills` (JSON), `created_at`.
- **`Resume`**: `id` (UUID), `filename`, `file_type`, `raw_text`, `candidate_name`, `email`, `extracted_data` (JSON), `extraction_status`, `uploaded_at`.
- **`MatchResult`**: `id` (UUID), `resume_id` (FK), `job_description_id` (FK, nullable), `evaluation_mode` ("role_match" / "general_quality"), `overall_score` (Integer 1-10), `matched_skills` (JSON), `missing_critical_skills` (JSON), `experience_fit_summary` (Text), `top_strengths` (JSON), `areas_for_improvement` (JSON), `primary_domain` (Text), `justification` (Text), `scored_at`.

---

## Setup and Quickstart

### 1. Activate Environment & Install Dependencies
```bash
cd "Smart Resume Scanner"
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Benchmark Evaluation
```bash
python eval.py
```

### 3. Launch Applications
```bash
# Terminal 1: Launch FastAPI Backend Server
uvicorn backend.app.main:app --reload --port 8000

# Terminal 2: Launch Streamlit Dashboard UI
streamlit run streamlit_app.py
```
- **Streamlit Dashboard**: [http://localhost:8501](http://localhost:8501)
- **FastAPI Web UI**: [http://localhost:8000](http://localhost:8000)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
# Smart-Resume-Scanner

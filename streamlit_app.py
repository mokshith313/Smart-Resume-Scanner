import streamlit as st
import pandas as pd
import requests
import os

# 1. APP CONFIGURATION & BRANDING
st.set_page_config(
    page_title="Smart Resume Screener",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1")

# Sidebar Configuration
st.sidebar.title("🎯 Smart Resume Screener")
st.sidebar.markdown("---")
st.sidebar.subheader("System Status")
st.sidebar.success("⚡ API Connected")
st.sidebar.info("🤖 Provider-Agnostic LLM Engine Active")

st.sidebar.markdown("---")
st.sidebar.subheader("Quick Presets")
preset = st.sidebar.selectbox("Load Sample JD Preset", ["Select Preset...", "Senior Backend Engineer", "Lead Data Scientist"])

# Initialize Session State
if "active_job_id" not in st.session_state:
    st.session_state.active_job_id = None
if "active_job_title" not in st.session_state:
    st.session_state.active_job_title = "General Resume Evaluation"
if "shortlist_data" not in st.session_state:
    st.session_state.shortlist_data = None
if "loaded_sample_files" not in st.session_state:
    st.session_state.loaded_sample_files = False

# App Header Banner
st.title("🎯 Smart Resume Screener v1.0")
st.caption("AI-Powered Resume Parsing, Skill Gap Analysis & Dual-Mode Semantic Matching")

# 2. TOP METRICS ROW (RESPONSIVE FLEX COLUMNS & TRUNCATION FIX)
m1, m2, m3, m4 = st.columns([1.5, 1, 1, 1])

total_screened = 0
top_score = "0 / 10"
avg_score = "0.0 / 10"

if st.session_state.shortlist_data:
    cands = st.session_state.shortlist_data.get("candidates", [])
    total_screened = len(cands)
    if cands:
        scores = [c["overall_score"] for c in cands]
        top_score = f"{max(scores)} / 10"
        avg_score = f"{round(sum(scores) / len(scores), 1)} / 10"

raw_job_title = st.session_state.active_job_title
display_job_title = (raw_job_title[:18] + "...") if len(raw_job_title) > 18 else raw_job_title

with m1:
    st.metric("ACTIVE JOB ROLE", display_job_title, help=raw_job_title)
with m2:
    st.metric("SCREENED RESUMES", total_screened)
with m3:
    st.metric("TOP MATCH SCORE", top_score)
with m4:
    st.metric("AVG FIT SCORE", avg_score)

st.markdown("---")

# Main Navigation Tabs
tab1, tab2, tab3 = st.tabs([
    "📥 Main Screener Dashboard",
    "🔍 Detailed Side-by-Side View",
    "⚙️ System & Prompt Transparency"
])

# ==========================================
# 3. MAIN 2-COLUMN DASHBOARD GRID (NATIVE CONTAINERS)
# ==========================================
with tab1:
    left_col, right_col = st.columns([1, 1], gap="medium")

    # LEFT COLUMN (left_col): Target Job Description + Resume Upload Cards
    with left_col:
        
        # CARD 1: Target Job Description & Strategy
        with st.container(border=True):
            st.subheader("1. Target Job Description & Strategy")
            
            mode_selection = st.radio(
                "Screening Mode Strategy",
                ["Mode A: Role-Specific Match (With Job Description)", "Mode B: General Profile Quality & Skill Index (Without Job Description)"],
                horizontal=True
            )
            is_mode_a = "Mode A" in mode_selection

            if is_mode_a:
                default_title = "Senior Backend Engineer" if preset == "Senior Backend Engineer" else ("Lead Data Scientist" if preset == "Lead Data Scientist" else "")
                default_company = "CloudScale Systems" if preset == "Senior Backend Engineer" else ("Insight AI" if preset == "Lead Data Scientist" else "")
                default_text = ""
                if preset == "Senior Backend Engineer":
                    default_text = "Required Skills: Python, FastAPI, PostgreSQL, Docker, AWS, REST APIs.\nResponsibilities: Design microservices, optimize SQL databases, deploy containerized cloud applications."
                elif preset == "Lead Data Scientist":
                    default_text = "Required Skills: Python, PyTorch, SQL, NLP, Machine Learning, AWS.\nResponsibilities: Train deep learning NLP models, build ETL data pipelines."

                jd_title = st.text_input("Job Title", value=default_title, placeholder="e.g. Senior Backend Engineer")
                jd_company = st.text_input("Company Name", value=default_company, placeholder="e.g. CloudScale Systems")
                jd_text = st.text_area("Job Requirements & Description Text", value=default_text, height=180, placeholder="Paste job description requirements...")

                if st.button("💾 Save Job Description", type="primary", use_container_width=True, key="save_jd_btn"):
                    if not jd_title.strip() or not jd_text.strip():
                        st.error("Please provide both a Job Title and Job Requirements text.")
                    else:
                        try:
                            res = requests.post(f"{API_BASE_URL}/jobs/", json={
                                "title": jd_title.strip(),
                                "company": jd_company.strip(),
                                "raw_text": jd_text.strip()
                            }, timeout=10)
                            if res.status_code == 201:
                                data = res.json()
                                st.session_state.active_job_id = data["id"]
                                st.session_state.active_job_title = data["title"]
                                st.success(f"Job Description Saved! ID: `{data['id']}`")
                            else:
                                st.error(f"Error saving job: {res.text}")
                        except (requests.exceptions.ConnectionError, requests.exceptions.RequestException):
                            st.error("⚠️ Backend server offline! Please start FastAPI via: uvicorn backend.app.main:app --reload --port 8000")
                        except Exception as e:
                            st.error(f"API Connection Error: {e}")
            else:
                st.info("ℹ️ Mode B evaluates overall resume impact, career progression clarity, technical skill density, and educational quality WITHOUT requiring a Job Description.")
                st.session_state.active_job_id = None
                st.session_state.active_job_title = "General Resume Evaluation"

        # CARD 2: Candidate Resume Upload
        with st.container(border=True):
            st.subheader("2. Upload Candidate Resumes")
            
            if st.button("⚡ Load 3 Sample Test Resumes", type="secondary", use_container_width=True, key="load_samples_btn"):
                st.session_state.loaded_sample_files = True
                st.success("Loaded 3 Synthetic Resumes (John Backend, Sarah DevOps PDF, Bob Frontend)!")

            uploaded_files = st.file_uploader(
                "Upload Candidate Resumes (PDF or TXT)",
                type=["pdf", "txt"],
                accept_multiple_files=True
            )

            has_resumes = bool(uploaded_files or st.session_state.get("loaded_sample_files", False))
            process_btn = st.button("🚀 Run AI Resume Screener", type="primary", use_container_width=True, disabled=not has_resumes, key="run_screener_btn")

            if process_btn:
                if is_mode_a and not st.session_state.active_job_id:
                    if jd_title.strip() and jd_text.strip():
                        try:
                            res = requests.post(f"{API_BASE_URL}/jobs/", json={
                                "title": jd_title.strip(),
                                "company": jd_company.strip(),
                                "raw_text": jd_text.strip()
                            }, timeout=10)
                            if res.status_code == 201:
                                data = res.json()
                                st.session_state.active_job_id = data["id"]
                                st.session_state.active_job_title = data["title"]
                        except Exception:
                            pass

                with st.spinner("Processing resumes... Parsing text, extracting structured profiles, and computing scores..."):
                    try:
                        files_payload = []
                        
                        if uploaded_files:
                            for f in uploaded_files:
                                files_payload.append(("files", (f.name, f.getvalue(), f.type or "application/octet-stream")))

                        if st.session_state.loaded_sample_files:
                            sample_paths = [
                                "samples/resumes/john_doe_backend.txt",
                                "samples/resumes/sarah_connor_devops.pdf",
                                "samples/resumes/bob_johnson_frontend.txt"
                            ]
                            for path in sample_paths:
                                if os.path.exists(path):
                                    with open(path, "rb") as sf:
                                        mime = "application/pdf" if path.endswith(".pdf") else "text/plain"
                                        files_payload.append(("files", (os.path.basename(path), sf.read(), mime)))

                        upload_res = requests.post(f"{API_BASE_URL}/resumes/upload", files=files_payload, timeout=30)
                        
                        if upload_res.status_code != 201:
                            st.error(f"Failed to upload resumes: {upload_res.text}")
                        else:
                            resumes_data = upload_res.json()
                            resume_ids = [r["id"] for r in resumes_data]

                            req_payload = {"resume_ids": resume_ids}
                            if is_mode_a:
                                req_payload["job_description_id"] = st.session_state.active_job_id

                            screen_res = requests.post(f"{API_BASE_URL}/screener/screen", json=req_payload, timeout=60)

                            if screen_res.status_code == 200:
                                st.session_state.shortlist_data = screen_res.json()
                                st.rerun()
                            else:
                                st.error(f"Screening failed: {screen_res.text}")

                    except (requests.exceptions.ConnectionError, requests.exceptions.RequestException):
                        st.error("⚠️ Backend server offline! Please start FastAPI via: uvicorn backend.app.main:app --reload --port 8000")
                    except Exception as e:
                        st.error(f"Error executing screening: {e}")

    # RIGHT COLUMN (right_col): Candidate Leaderboard Card
    with right_col:
        with st.container(border=True):
            st.subheader("🏆 Candidate Fit Leaderboard")

            if not st.session_state.shortlist_data:
                st.info("No candidates screened yet. Upload resumes and run screening on the left panel.")
            else:
                shortlist = st.session_state.shortlist_data
                candidates = shortlist.get("candidates", [])
                mode = shortlist.get("evaluation_mode", "role_match")
                
                st.caption(f"Evaluation Mode: `{mode.upper()}` | Context: `{shortlist.get('job_title')}` | Total: {len(candidates)}")

                for idx, c in enumerate(candidates):
                    rank = f"#{idx + 1}"
                    score = c["overall_score"]
                    name = c["candidate_name"]
                    email = c.get("candidate_email") or "No email listed"
                    skills = (c.get("extracted_data") or {}).get("skills", [])
                    primary_skills_str = ", ".join(skills[:4]) if skills else "General Profile"

                    score_emoji = "🟢" if score >= 8 else ("🟡" if score >= 6 else "🔴")
                    card_title = f"{rank} {name} — Fit Score: {score}/10 {score_emoji} | {primary_skills_str}"

                    with st.expander(card_title, expanded=(idx == 0)):
                        if mode == "role_match":
                            st.markdown("#### 🎯 Role Skill Matrix (Mode A)")
                            st.write("**Matched Skills:**", ", ".join(c.get("matched_skills", [])) or "None")
                            st.write("**Missing Critical Skills:**", ", ".join(c.get("missing_critical_skills", [])) or "None identified")
                            st.write("**Experience Fit:**", c.get("experience_fit_summary") or "N/A")
                        else:
                            st.markdown("#### 🌟 Profile Strengths & Gaps (Mode B)")
                            st.write("**Primary Domain:**", f"`{c.get('primary_domain')}`")
                            st.write("**Top Strengths:**")
                            for s in c.get("top_strengths", []):
                                st.caption(f"• {s}")
                            st.write("**Areas for Improvement:**")
                            for a in c.get("areas_for_improvement", []):
                                st.caption(f"• {a}")

                        st.markdown("#### 📝 Full LLM Score Justification")
                        st.info(c["justification"])


# ==========================================
# TAB 2: DETAILED CANDIDATE VIEW
# ==========================================
with tab2:
    st.subheader("🔍 Side-by-Side Detailed Candidate View")

    if not st.session_state.shortlist_data or not st.session_state.shortlist_data.get("candidates"):
        st.info("No candidate data available. Run screening in Tab 1.")
    else:
        candidates = st.session_state.shortlist_data["candidates"]
        cand_map = {c["candidate_name"]: c for c in candidates}
        selected_name = st.selectbox("Select Candidate", list(cand_map.keys()))
        cand = cand_map[selected_name]

        col_l, col_r = st.columns([1, 1], gap="large")

        with col_l:
            st.markdown("### 📊 Scoring Rationale & Matrix")
            st.metric("Overall Score", f"{cand['overall_score']} / 10")
            st.markdown(f"**Justification:** {cand['justification']}")

        with col_r:
            st.markdown("### 📄 Parsed Resume Sections")
            ext = cand.get("extracted_data") or {}
            st.write("**Skills:**", ", ".join(ext.get("skills", [])))
            st.write("**Work Experience:**")
            for e in ext.get("experience", []):
                st.caption(f"• {e.get('role')} at {e.get('company')} ({e.get('duration')})")


# ==========================================
# TAB 3: SYSTEM & PROMPT TRANSPARENCY
# ==========================================
with tab3:
    st.subheader("⚙️ System & Prompt Transparency")
    st.caption("Verbatim LLM Prompt Engineering Specs and Strict Pydantic JSON Output Schemas")

    with st.expander("📄 1. Resume Profile Extraction Prompt & Schema", expanded=True):
        st.markdown("**System Prompt:** `You are an expert ATS data extraction system...`")
        st.code("""
{
  "candidate_name": "Full Name",
  "contact_info": { "email": "email@example.com", "phone": "555-0192" },
  "skills": ["Python", "FastAPI", "PostgreSQL"],
  "experience": [{ "role": "Senior Dev", "company": "TechCorp", "duration": "2021-2024", "responsibilities": "..." }],
  "education": [{ "degree": "B.S. CS", "institution": "MIT", "year": "2021" }]
}
        """, language="json")

    with st.expander("🎯 2. Mode A: Role-Specific Match Prompt & Schema", expanded=False):
        st.markdown("**User Prompt Pattern:** `Compare the candidate's structured resume against the target job description...`")
        st.code("""
{
  "evaluation_mode": "role_match",
  "overall_score": 8,
  "matched_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
  "missing_critical_skills": ["Kubernetes", "AWS"],
  "experience_fit_summary": "5+ years of relevant experience building Python microservices.",
  "justification": "Candidate demonstrates strong fit..."
}
        """, language="json")

    with st.expander("🌟 3. Mode B: General Resume Quality Prompt & Schema", expanded=False):
        st.markdown("**User Prompt Pattern:** `Evaluate general candidate resume profile strength, skill density, and progression without a JD...`")
        st.code("""
{
  "evaluation_mode": "general_quality",
  "overall_score": 8,
  "top_strengths": ["High technical skill density", "Clear career progression"],
  "areas_for_improvement": ["Add quantitative metrics"],
  "primary_domain": "Backend Software Engineering",
  "justification": "Candidate presents a well-structured resume..."
}
        """, language="json")

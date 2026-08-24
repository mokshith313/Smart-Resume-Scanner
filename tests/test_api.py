import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.database import Base, engine

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_job_description_crud():
    response = client.post("/api/v1/jobs/", json={
        "title": "Senior Python Developer",
        "company": "Tech Corp",
        "raw_text": "Need Python, FastAPI, PostgreSQL, Docker."
    })
    assert response.status_code == 201
    job_data = response.json()
    assert job_data["title"] == "Senior Python Developer"
    job_id = job_data["id"]

    list_res = client.get("/api/v1/jobs/")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    get_res = client.get(f"/api/v1/jobs/{job_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == job_id


def test_resume_upload_and_screening_workflow():
    # 1. Create Job
    job_res = client.post("/api/v1/jobs/", json={
        "title": "Senior Backend Engineer",
        "company": "Cloud Corp",
        "raw_text": "Required skills: Python, FastAPI, Docker, PostgreSQL."
    })
    assert job_res.status_code == 201
    job_id = job_res.json()["id"]

    # 2. Upload Resume Files
    with open("samples/resumes/john_doe_backend.txt", "rb") as f1, \
         open("samples/resumes/sarah_connor_devops.pdf", "rb") as f2:
        upload_res = client.post("/api/v1/resumes/upload", files=[
            ("files", ("john_doe_backend.txt", f1, "text/plain")),
            ("files", ("sarah_connor_devops.pdf", f2, "application/pdf"))
        ])

    assert upload_res.status_code == 201
    uploaded_resumes = upload_res.json()
    assert len(uploaded_resumes) == 2
    resume_ids = [r["id"] for r in uploaded_resumes]

    # 3. Trigger Batch Screening
    screen_res = client.post("/api/v1/screener/screen", json={
        "job_description_id": job_id,
        "resume_ids": resume_ids
    })
    assert screen_res.status_code == 200
    shortlist = screen_res.json()
    assert shortlist["total_screened"] == 2
    assert len(shortlist["candidates"]) == 2

    # Verify overall_score ranking descending order
    cands = shortlist["candidates"]
    assert cands[0]["overall_score"] >= cands[1]["overall_score"]
    assert len(cands[0]["justification"]) > 0

    # 4. Fetch Ranked Shortlist via GET endpoint
    get_shortlist = client.get(f"/api/v1/screener/shortlist/{job_id}")
    assert get_shortlist.status_code == 200
    assert len(get_shortlist.json()["candidates"]) == 2

    # Test filtering by score
    filtered_res = client.get(f"/api/v1/screener/shortlist/{job_id}?min_score=9")
    assert filtered_res.status_code == 200

    # 5. Fetch Match Rationale Detail
    match_id = cands[0]["id"]
    match_detail = client.get(f"/api/v1/screener/match/{match_id}")
    assert match_detail.status_code == 200
    assert match_detail.json()["id"] == match_id

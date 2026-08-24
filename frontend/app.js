// Application State
let currentJobId = null;
let selectedFiles = [];
let allScreenedCandidates = [];
let candidateModalInstance = null;

// Sample Job Descriptions
const SAMPLE_JDS = {
    backend: {
        title: "Senior Backend Engineer",
        company: "CloudScale Systems",
        text: `We are looking for a Senior Backend Engineer to join our core cloud platform team.
Key Responsibilities:
- Design, build, and maintain high-performance microservices in Python and FastAPI.
- Manage PostgreSQL, Redis, and MongoDB databases for scalable storage.
- Containerize services with Docker and manage deployments using Kubernetes on AWS.
- Implement CI/CD pipelines, automated testing, and REST APIs.

Requirements:
- 4+ years of professional experience in Python, FastAPI or Django.
- Hands-on experience with SQL databases (PostgreSQL), Docker, and Git.
- Exposure to cloud platforms (AWS/GCP) and container orchestration (Kubernetes).
- Bachelor's degree in Computer Science or equivalent practical experience.`
    }
};

document.addEventListener("DOMContentLoaded", () => {
    candidateModalInstance = new bootstrap.Modal(document.getElementById('candidateModal'));
    setupDropZone();
});

function loadSampleJD(key) {
    const sample = SAMPLE_JDS[key];
    if (sample) {
        document.getElementById('jdTitle').value = sample.title;
        document.getElementById('jdCompany').value = sample.company;
        document.getElementById('jdText').value = sample.text;
    }
}

async function saveJobDescription() {
    const title = document.getElementById('jdTitle').value.trim();
    const company = document.getElementById('jdCompany').value.trim();
    const raw_text = document.getElementById('jdText').value.trim();

    if (!title || !raw_text) {
        alert("Please enter both a Job Title and Job Requirements text.");
        return;
    }

    const btn = document.getElementById('btnSaveJD');
    btn.disabled = true;
    btn.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>Saving...`;

    try {
        const response = await fetch('/api/v1/jobs/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, company, raw_text })
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "Failed to save Job Description");
        }

        const data = await response.json();
        currentJobId = data.id;
        document.getElementById('metricActiveJob').textContent = `${data.title} (${data.company})`;

        btn.className = "btn btn-success w-100 fw-semibold";
        btn.innerHTML = `<i class="bi bi-check-circle-fill me-1"></i>Active: ${data.title}`;
        
        updateScreenButtonState();

    } catch (err) {
        alert(`Error saving JD: ${err.message}`);
        btn.disabled = false;
        btn.innerHTML = `<i class="bi bi-check-circle me-1"></i>Save Job Description`;
    }
}

function setupDropZone() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        }, false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        handleFiles(dt.files);
    });

    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });
}

function handleFiles(files) {
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        if (file.name.endsWith('.pdf') || file.name.endsWith('.txt')) {
            // Avoid duplicates
            if (!selectedFiles.some(f => f.name === file.name)) {
                selectedFiles.push(file);
            }
        }
    }
    renderFileList();
    updateScreenButtonState();
}

function renderFileList() {
    const listContainer = document.getElementById('fileList');
    if (selectedFiles.length === 0) {
        listContainer.innerHTML = '';
        return;
    }

    let html = `<div class="fw-semibold text-dark mb-1">Queue (${selectedFiles.length} files):</div><ul class="list-group list-group-flush border rounded-2">`;
    selectedFiles.forEach((file, index) => {
        const icon = file.name.endsWith('.pdf') ? 'file-earmark-pdf-fill text-danger' : 'file-earmark-text-fill text-primary';
        const sizeKB = (file.size / 1024).toFixed(1);
        html += `
            <li class="list-group-item d-flex justify-content-between align-items-center py-2 px-3">
                <span><i class="bi bi-${icon} me-2"></i><strong>${file.name}</strong> <span class="text-muted">(${sizeKB} KB)</span></span>
                <i class="bi bi-trash text-muted cursor-pointer hover-danger" onclick="removeFile(${index})"></i>
            </li>
        `;
    });
    html += '</ul>';
    listContainer.innerHTML = html;
}

function removeFile(index) {
    selectedFiles.splice(index, 1);
    renderFileList();
    updateScreenButtonState();
}

function updateScreenButtonState() {
    const btnScreen = document.getElementById('btnScreen');
    btnScreen.disabled = !(currentJobId && selectedFiles.length > 0);
}

async function uploadAndScreenResumes() {
    if (!currentJobId || selectedFiles.length === 0) return;

    const spinner = document.getElementById('screeningSpinner');
    const emptyState = document.getElementById('emptyState');
    const candidateList = document.getElementById('candidateList');
    const btnScreen = document.getElementById('btnScreen');

    btnScreen.disabled = true;
    spinner.classList.remove('d-none');
    emptyState.classList.add('d-none');
    candidateList.innerHTML = '';

    try {
        // Step 1: Upload Resumes
        const formData = new FormData();
        selectedFiles.forEach(file => formData.append('files', file));

        const uploadRes = await fetch('/api/v1/resumes/upload', {
            method: 'POST',
            body: formData
        });

        if (!uploadRes.ok) {
            throw new Error("Failed to upload resumes.");
        }

        const uploadedResumes = await uploadRes.json();
        const resumeIds = uploadedResumes.map(r => r.id);

        // Step 2: Trigger AI Screening against current Job ID
        const screenRes = await fetch('/api/v1/screener/screen', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                job_description_id: currentJobId,
                resume_ids: resumeIds
            })
        });

        if (!screenRes.ok) {
            throw new Error("AI screening failed.");
        }

        const shortlistData = await screenRes.json();
        allScreenedCandidates = shortlistData.candidates;

        // Render Leaderboard & Metrics
        renderMetrics(allScreenedCandidates);
        filterShortlist();

    } catch (err) {
        alert(`Screening Error: ${err.message}`);
    } finally {
        spinner.classList.add('d-none');
        btnScreen.disabled = false;
    }
}

function renderMetrics(candidates) {
    document.getElementById('metricTotalScreened').textContent = candidates.length;
    if (candidates.length === 0) {
        document.getElementById('metricTopScore').textContent = '0.0 / 10';
        document.getElementById('metricAvgScore').textContent = '0.0 / 10';
        return;
    }

    const scores = candidates.map(c => c.score);
    const topScore = Math.max(...scores);
    const avgScore = (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(1);

    document.getElementById('metricTopScore').textContent = `${topScore.toFixed(1)} / 10`;
    document.getElementById('metricAvgScore').textContent = `${avgScore} / 10`;
}

function filterShortlist() {
    const searchVal = document.getElementById('searchFilter').value.toLowerCase().trim();
    const minScore = parseFloat(document.getElementById('scoreFilter').value) || 0;

    const filtered = allScreenedCandidates.filter(c => {
        const scorePass = c.score >= minScore;
        const searchPass = !searchVal || 
            c.candidate_name.toLowerCase().includes(searchVal) ||
            (c.extracted_data && c.extracted_data.skills.some(s => s.toLowerCase().includes(searchVal)));
        return scorePass && searchPass;
    });

    renderCandidateLeaderboard(filtered);
}

function renderCandidateLeaderboard(candidates) {
    const container = document.getElementById('candidateList');
    const emptyState = document.getElementById('emptyState');

    if (candidates.length === 0) {
        container.innerHTML = '';
        emptyState.classList.remove('d-none');
        return;
    }

    emptyState.classList.add('d-none');
    let html = '';

    candidates.forEach((c, index) => {
        const rank = index + 1;
        let borderClass = '';
        let rankBadgeClass = 'badge-rank-other';
        if (rank === 1) { borderClass = 'border-gold'; rankBadgeClass = 'badge-rank-1'; }
        else if (rank === 2) { borderClass = 'border-silver'; rankBadgeClass = 'badge-rank-2'; }
        else if (rank === 3) { borderClass = 'border-bronze'; rankBadgeClass = 'badge-rank-3'; }

        let scoreClass = 'score-high';
        if (c.score < 6.0) scoreClass = 'score-low';
        else if (c.score < 8.0) scoreClass = 'score-medium';

        // Render skill tags
        const skills = c.extracted_data ? c.extracted_data.skills.slice(0, 6) : [];
        const matchedSkills = c.skills_match ? (c.skills_match.matched_skills || []) : [];
        
        let skillBadgesHtml = skills.map(skill => {
            const isMatched = matchedSkills.some(m => m.toLowerCase() === skill.toLowerCase());
            const tagClass = isMatched ? 'skill-matched' : 'skill-general';
            return `<span class="skill-tag ${tagClass} me-1 mb-1">${skill}</span>`;
        }).join('');

        html += `
            <div class="card candidate-card shadow-sm border-0 ${borderClass} rounded-3 p-3">
                <div class="d-flex align-items-start justify-content-between gap-3">
                    <div class="d-flex align-items-center gap-3">
                        <div class="rank-pill ${rankBadgeClass}">#${rank}</div>
                        <div>
                            <h6 class="fw-bold m-0 text-dark">${c.candidate_name}</h6>
                            <div class="text-muted small">${c.candidate_email || 'No email specified'}</div>
                        </div>
                    </div>
                    <div class="score-badge ${scoreClass}">
                        <span>${c.score.toFixed(1)}</span>
                        <span style="font-size: 0.65rem; font-weight: 500;">/ 10</span>
                    </div>
                </div>

                <div class="mt-3">
                    <div class="text-muted small fw-semibold mb-1">KEY EXTRACTED SKILLS</div>
                    <div class="d-flex flex-wrap">${skillBadgesHtml || '<span class="text-muted small">No explicit skills listed</span>'}</div>
                </div>

                <div class="mt-3 pt-2 border-top d-flex justify-content-between align-items-center">
                    <div class="text-muted small text-truncate max-w-400 me-2">
                        <i class="bi bi-chat-left-quote me-1"></i>${c.justification.substring(0, 110)}...
                    </div>
                    <button class="btn btn-sm btn-outline-primary fw-semibold text-nowrap rounded-pill px-3" onclick="openCandidateModal('${c.id}')">
                        View Full Rationale <i class="bi bi-chevron-right ms-1"></i>
                    </button>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}

function openCandidateModal(matchId) {
    const candidate = allScreenedCandidates.find(c => c.id === matchId);
    if (!candidate) return;

    document.getElementById('modalCandidateName').textContent = `${candidate.candidate_name} — Score Rationale`;

    const matchedList = candidate.skills_match.matched_skills || [];
    const missingList = candidate.skills_match.missing_skills || [];
    const coveragePct = candidate.skills_match.coverage_percentage || 0;

    let strengthsHtml = (candidate.strengths || []).map(s => `<li class="mb-1"><i class="bi bi-check-circle-fill text-success me-2"></i>${s}</li>`).join('');
    let gapsHtml = (candidate.gaps || []).map(g => `<li class="mb-1"><i class="bi bi-exclamation-triangle-fill text-warning me-2"></i>${g}</li>`).join('');

    let expHtml = '';
    if (candidate.extracted_data && candidate.extracted_data.experience) {
        expHtml = candidate.extracted_data.experience.map(e => `
            <div class="mb-2 p-2 bg-light rounded border-start border-3 border-primary">
                <div class="fw-bold small text-dark">${e.role} — <span class="text-muted">${e.company}</span></div>
                <div class="text-muted text-xs mb-1"><i class="bi bi-calendar3 me-1"></i>${e.duration}</div>
                <div class="small text-secondary">${e.responsibilities}</div>
            </div>
        `).join('');
    }

    let eduHtml = '';
    if (candidate.extracted_data && candidate.extracted_data.education) {
        eduHtml = candidate.extracted_data.education.map(ed => `
            <div class="small fw-semibold text-dark"><i class="bi bi-mortarboard-fill text-primary me-2"></i>${ed.degree} — <span class="text-muted">${ed.institution} (${ed.year})</span></div>
        `).join('');
    }

    document.getElementById('modalBodyContent').innerHTML = `
        <div class="row g-3 mb-4">
            <div class="col-md-4">
                <div class="p-3 bg-light rounded-3 text-center border">
                    <div class="text-muted small fw-semibold">FIT MATCH SCORE</div>
                    <div class="display-6 fw-bold text-primary mt-1">${candidate.score.toFixed(1)} <span class="fs-5 text-muted">/ 10</span></div>
                </div>
            </div>
            <div class="col-md-8">
                <div class="p-3 bg-light rounded-3 border">
                    <div class="d-flex justify-content-between small fw-semibold mb-1">
                        <span>REQUIRED SKILL COVERAGE</span>
                        <span>${coveragePct}%</span>
                    </div>
                    <div class="progress" style="height: 10px;">
                        <div class="progress-bar bg-success" role="progressbar" style="width: ${coveragePct}%"></div>
                    </div>
                    <div class="mt-2 small">
                        <span class="text-success fw-semibold">Matched:</span> ${matchedList.join(', ') || 'None'}
                    </div>
                    <div class="small">
                        <span class="text-danger fw-semibold">Missing:</span> ${missingList.join(', ') || 'None identified'}
                    </div>
                </div>
            </div>
        </div>

        <div class="mb-4">
            <h6 class="fw-bold text-dark border-bottom pb-2"><i class="bi bi-file-text-fill text-primary me-2"></i>AI Justification & Evidence</h6>
            <p class="text-secondary leading-relaxed bg-light p-3 rounded-3 border">${candidate.justification}</p>
        </div>

        <div class="row g-3 mb-4">
            <div class="col-md-6">
                <h6 class="fw-bold text-success border-bottom pb-2"><i class="bi bi-hand-thumbs-up-fill me-2"></i>Candidate Strengths</h6>
                <ul class="list-unstyled small">${strengthsHtml || '<li>No explicit strengths recorded</li>'}</ul>
            </div>
            <div class="col-md-6">
                <h6 class="fw-bold text-warning border-bottom pb-2"><i class="bi bi-exclamation-circle-fill me-2"></i>Skill Gaps / Risks</h6>
                <ul class="list-unstyled small">${gapsHtml || '<li>No explicit gaps recorded</li>'}</ul>
            </div>
        </div>

        <div class="mb-3">
            <h6 class="fw-bold text-dark border-bottom pb-2"><i class="bi bi-briefcase-fill text-primary me-2"></i>Extracted Work Experience</h6>
            ${expHtml || '<div class="text-muted small">No work experience extracted</div>'}
        </div>

        <div>
            <h6 class="fw-bold text-dark border-bottom pb-2"><i class="bi bi-building me-2"></i>Extracted Education</h6>
            ${eduHtml || '<div class="text-muted small">No education history extracted</div>'}
        </div>
    `;

    candidateModalInstance.show();
}

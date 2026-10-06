import pytest

from models import Candidate, GitHubAnalysis, ResumeAnalysis, db
from tasks.resume_tasks import _extract_pdf_text, process_resume_task


@pytest.fixture
def provider_result():
    return {
        "ats_score": 70,
        "breakdown": {"keyword_match": 20, "skills_alignment": 10, "experience_relevance": 15,
                      "education": 5, "formatting": 5, "achievements": 5, "completeness": 10},
        "missing_keywords": ["PostgreSQL"], "weak_areas": ["Deployment evidence is missing"],
        "top_improvements": ["Describe test coverage"], "projects": ["Flask API"],
        "final_verdict": "Relevant Python evidence; recruiter should verify deployment experience.",
    }


@pytest.fixture
def fake_provider(monkeypatch, provider_result):
    calls = []

    def generate(prompt, schema):
        calls.append((prompt, schema))
        return provider_result, "mock-gemini"

    monkeypatch.setattr("services.resume.analyzer.generate_json", generate)
    monkeypatch.setattr("tasks.resume_tasks._extract_pdf_text", lambda _: "Test Applicant Python Flask experience")
    return calls


def test_parser_valid_blank_pdf(tmp_path, pdf_bytes):
    path = tmp_path / "resume.pdf"
    path.write_bytes(pdf_bytes)
    assert _extract_pdf_text(str(path)) == ""


def test_job_aware_partial_analysis_and_sequential_redelivery(apply, app, client, fake_provider):
    candidate_id = apply().json["candidateId"]
    queued = client.get(f"/api/candidates/{candidate_id}/analysis").json
    assert queued["status"] == "queued"
    assert queued["resume"]["status"] == queued["github"]["status"] == "pending"
    with app.app_context():
        assert process_resume_task.run(candidate_id)["status"] == "partial"
        candidate = db.session.get(Candidate, candidate_id)
        assert candidate.raw_text.startswith("Test Applicant")
        assert candidate.status == "screening"
        assert candidate.ats_score == 70
        assert candidate.resume_analysis.model_name == "mock-gemini"
        process_resume_task.run(candidate_id)
        assert Candidate.query.count() == ResumeAnalysis.query.count() == GitHubAnalysis.query.count() == 1
    assert len(fake_provider) == 1
    assert "Test Engineering Role" in fake_provider[0][0]
    assert "Build tested Python systems." in fake_provider[0][0]
    assert '"languages": ["Python"]' in fake_provider[0][0]
    assert '"frameworks": ["Flask"]' in fake_provider[0][0]
    result = client.get(f"/api/candidates/{candidate_id}/analysis").json
    assert result["resume"]["breakdown"]["keyword_match"] == 20
    assert result["github"]["status"] == "failed"
    assert result["github"]["total_stars"] is None
    assert "could not be reached" in result["github"]["error_message"]
    assert "file_path" not in str(result)
    assert client.post(f"/api/candidates/{candidate_id}/analysis/retry").status_code == 202
    with app.app_context():
        assert db.session.get(Candidate, candidate_id).resume_analysis.status == "complete"
        assert process_resume_task.run(candidate_id)["status"] == "partial"
    assert len(fake_provider) == 1


def test_optional_github_complete_and_completed_redelivery(apply, app, client, fake_provider):
    candidate_id = apply(github_username="").json["candidateId"]
    with app.app_context():
        assert process_resume_task.run(candidate_id)["status"] == "complete"
        assert process_resume_task.run(candidate_id)["status"] == "complete"
        assert db.session.get(Candidate, candidate_id).status == "screening"
    assert len(fake_provider) == 1
    result = client.get(f"/api/candidates/{candidate_id}/analysis").json
    assert result["github"] is None
    assert result["error_message"] is None
    assert client.post(f"/api/candidates/{candidate_id}/analysis/retry").status_code == 409


def test_parser_failure_can_recover(apply, app, client, monkeypatch, fake_provider):
    candidate_id = apply(b"%PDF-malformed").json["candidateId"]
    def broken_parser(_):
        raise ValueError("private-file-path provider-secret")
    monkeypatch.setattr("tasks.resume_tasks._extract_pdf_text", broken_parser)
    with app.app_context():
        result = process_resume_task.run(candidate_id)
        assert result["status"] == "failed"
        assert "error" not in result
        candidate = db.session.get(Candidate, candidate_id)
        assert candidate.status == "screening"
        assert candidate.resume_analysis.status == "failed"
        assert candidate.ats_score is None
    response = client.get(f"/api/candidates/{candidate_id}/analysis")
    assert "private-file-path" not in str(response.json)
    assert "provider-secret" not in str(response.json)
    assert client.post(f"/api/candidates/{candidate_id}/analysis/retry").status_code == 202
    monkeypatch.setattr("tasks.resume_tasks._extract_pdf_text", lambda _: "Recovered resume text")
    with app.app_context():
        assert process_resume_task.run(candidate_id)["status"] == "partial"
        assert db.session.get(Candidate, candidate_id).status == "screening"
    assert len(fake_provider) == 1


def test_missing_key_saves_failure_and_preserves_extracted_text(apply, app, client, monkeypatch):
    candidate_id = apply(github_username="").json["candidateId"]
    monkeypatch.setattr("tasks.resume_tasks._extract_pdf_text", lambda _: "Readable resume")
    with app.app_context():
        assert process_resume_task.run(candidate_id)["status"] == "failed"
        candidate = db.session.get(Candidate, candidate_id)
        assert candidate.raw_text == "Readable resume"
        assert candidate.status == "screening"
        assert candidate.ats_score is None
    result = client.get(f"/api/candidates/{candidate_id}/analysis").json
    assert "not configured" in result["resume"]["error_message"]
    assert result["resume"]["ats_score"] is None


def test_invalid_provider_output_clears_stale_scores(apply, app, fake_provider, provider_result):
    candidate_id = apply().json["candidateId"]
    provider_result["ats_score"] = 101
    with app.app_context():
        candidate = db.session.get(Candidate, candidate_id)
        candidate.ats_score = candidate.resume_analysis.ats_score = 50
        db.session.commit()
        assert process_resume_task.run(candidate_id)["status"] == "failed"
        assert candidate.ats_score is None
        assert candidate.resume_analysis.ats_score is None
        assert candidate.resume_analysis.breakdown is None
        assert "invalid score" in candidate.resume_analysis.error_message
        assert candidate.status == "screening"


def test_provider_exception_is_not_exposed(apply, app, client, fake_provider, monkeypatch):
    def fail(*_):
        raise RuntimeError("live-key /private/path traceback")
    monkeypatch.setattr("services.resume.analyzer.generate_json", fail)
    candidate_id = apply().json["candidateId"]
    with app.app_context():
        assert process_resume_task.run(candidate_id)["status"] == "failed"
    result = client.get(f"/api/candidates/{candidate_id}/analysis").json
    assert "live-key" not in str(result)
    assert "/private/path" not in str(result)
    assert "traceback" not in str(result)


def test_unknown_worker_candidate(app):
    with app.app_context():
        assert process_resume_task.run(999999)["status"] == "not_found"

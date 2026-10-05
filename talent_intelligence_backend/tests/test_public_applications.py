import io
from pathlib import Path
from types import SimpleNamespace

import pytest

from models import Candidate, db
from routes.application_routes import MAX_RESUME_BYTES
from services.analysis_queue import process_resume_task


def test_unknown_job(client):
    assert client.post("/api/public/jobs/999/apply").status_code == 404


def test_missing_resume(apply):
    assert apply(filename=None).status_code == 400


@pytest.mark.parametrize("content,filename,mimetype", [
    (b"text", "resume.txt", "text/plain"),
    (b"not a pdf", "resume.pdf", "application/pdf"),
    (b"%PDF-1.4", "resume.pdf", "text/html"),
])
def test_invalid_pdf(apply, content, filename, mimetype):
    assert apply(content, filename, mimetype).status_code == 400


def test_oversize_pdf(apply, app):
    response = apply(b"%PDF-" + b"x" * MAX_RESUME_BYTES)
    assert response.status_code == 413
    assert response.json["error"]["code"] == "resume_too_large"
    with app.app_context():
        assert Candidate.query.count() == 0


def test_exact_upload_limit(apply):
    assert apply(b"%PDF-" + b"x" * (MAX_RESUME_BYTES - 5)).status_code == 200


def test_valid_application_persists_one_resume(apply, client, job_id, app):
    response = apply(filename="../../resume.pdf")
    assert response.status_code == 200
    assert response.json["status"] == "screening"
    assert response.json["analysis_status"] == "queued"
    applicants = client.get(f"/api/jobs/{job_id}/applicants").json["applicants"]
    assert len(applicants) == 1
    assert applicants[0]["filename"] == "resume.pdf"
    assert applicants[0]["allowed_actions"] == ["interview_scheduled", "rejected"]
    assert "file_path" not in applicants[0]
    assert "raw_text" not in applicants[0]
    assert len(list(Path(app.config["UPLOAD_FOLDER"]).iterdir())) == 1


def test_legacy_alias(apply, job_id):
    assert apply(endpoint=f"/api/jobs/{job_id}/apply").status_code == 200


def test_closed_application(client, job_id, apply):
    client.patch(f"/api/jobs/{job_id}", json={"status": "closed"})
    assert apply().status_code == 409


def test_optional_github(client, job_id, pdf_bytes):
    response = client.post(f"/api/public/jobs/{job_id}/apply", data={
        "full_name": "Test Applicant", "email": "applicant@example.invalid",
        "resume": (io.BytesIO(pdf_bytes), "resume.pdf"),
    })
    assert response.status_code == 200


def test_queue_failure_and_retry(apply, client, app, monkeypatch):
    def fail(*_):
        raise ConnectionError("redis://secret@private-host:6379/internal")
    monkeypatch.setattr(process_resume_task, "delay", fail)
    response = apply()
    assert response.status_code == 200
    assert response.json["success"] is True
    assert response.json["analysis_status"] == "enqueue_failed"
    candidate_id = response.json["candidateId"]
    with app.app_context():
        candidate = db.session.get(Candidate, candidate_id)
        assert candidate.status == "screening"
        assert "secret" not in candidate.analysis_error
        assert Candidate.query.count() == 1
    retry = client.post(f"/api/candidates/{candidate_id}/analysis/retry")
    assert retry.status_code == 503
    monkeypatch.setattr(process_resume_task, "delay", lambda *_: SimpleNamespace(id="retry-task"))
    retry = client.post(f"/api/candidates/{candidate_id}/analysis/retry")
    assert retry.status_code == 202
    assert retry.json["analysis_status"] == "queued"
    assert client.post(f"/api/candidates/{candidate_id}/analysis/retry").status_code == 409
    assert "secret" not in str(client.get(f"/api/candidates/{candidate_id}").json)

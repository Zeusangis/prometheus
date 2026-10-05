from models import Candidate, db
from tasks.resume_tasks import _extract_pdf_text, process_resume_task


def test_parser_valid_blank_pdf(tmp_path, pdf_bytes):
    path = tmp_path / "resume.pdf"
    path.write_bytes(pdf_bytes)
    assert _extract_pdf_text(str(path)) == ""


def test_extraction_is_partial_and_does_not_move_stage(apply, app, monkeypatch):
    candidate_id = apply().json["candidateId"]
    monkeypatch.setattr("tasks.resume_tasks._extract_pdf_text", lambda _: "Test Applicant Python Flask experience")
    with app.app_context():
        result = process_resume_task.run(candidate_id)
        assert result["status"] == "partial"
        candidate = db.session.get(Candidate, candidate_id)
        assert candidate.raw_text.startswith("Test Applicant")
        assert candidate.status == "screening"
        assert candidate.ats_score is None
        assert "not configured" in candidate.analysis_error
        process_resume_task.run(candidate_id)
        assert Candidate.query.count() == 1


def test_parser_failure_can_recover(apply, app, client, monkeypatch):
    candidate_id = apply(b"%PDF-malformed").json["candidateId"]
    with app.app_context():
        result = process_resume_task.run(candidate_id)
        assert result["status"] == "failed"
        assert "error" not in result
        candidate = db.session.get(Candidate, candidate_id)
        assert candidate.status == "screening"
        assert candidate.analysis_status == "failed"
    assert client.post(f"/api/candidates/{candidate_id}/analysis/retry").status_code == 202
    monkeypatch.setattr("tasks.resume_tasks._extract_pdf_text", lambda _: "Recovered resume text")
    with app.app_context():
        assert process_resume_task.run(candidate_id)["status"] == "partial"
        assert db.session.get(Candidate, candidate_id).status == "screening"

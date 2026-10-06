"""Operators and recruiters must be able to see why analysis cannot run."""

from models import Candidate, db
from tasks.resume_tasks import process_resume_task


def test_health_reports_resume_provider_readiness(app, client):
    payload = client.get("/api/health").json
    assert payload["service"] == "TrueHire"
    assert payload["resume_provider_configured"] is False
    assert payload["resume_model"]


def test_health_reports_configured_provider(app, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-placeholder")
    monkeypatch.setenv("GEMINI_MODEL", "configured-test-model")
    payload = app.test_client().get("/api/health").json
    assert payload["resume_provider_configured"] is True
    assert payload["resume_model"] == "configured-test-model"


def test_health_never_exposes_the_key(app, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "sentinel-secret-value")
    body = app.test_client().get("/api/health").get_data(as_text=True)
    assert "sentinel-secret-value" not in body


def test_check_analysis_command_explains_missing_key(app, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    result = app.test_cli_runner().invoke(args=["check-analysis"])
    assert result.exit_code == 0
    assert "GEMINI_API_KEY: MISSING" in result.output
    assert "resume analysis will fail for every applicant" in result.output


def test_check_analysis_command_never_prints_the_key(app, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "sentinel-secret-value")
    result = app.test_cli_runner().invoke(args=["check-analysis"])
    assert result.exit_code == 0
    assert "GEMINI_API_KEY: configured" in result.output
    assert "sentinel-secret-value" not in result.output


def test_check_analysis_command_reports_a_live_call_failure(app, monkeypatch):
    # With a placeholder key the live call must fail cleanly, not crash the CLI.
    monkeypatch.setenv("GEMINI_API_KEY", "test-only-placeholder")
    result = app.test_cli_runner().invoke(args=["check-analysis", "--live"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "Live provider call" in result.output


def test_analysis_endpoint_exposes_extracted_resume_text(apply, app, client, monkeypatch):
    candidate_id = apply().json["candidateId"]
    monkeypatch.setattr("services.resume.analyzer.generate_json", lambda *_: (_ for _ in ()).throw(
        RuntimeError("provider down")
    ))
    monkeypatch.setattr("tasks.resume_tasks._extract_pdf_text", lambda _: "Ada Example Python Flask")
    with app.app_context():
        process_resume_task.run(candidate_id)
        assert db.session.get(Candidate, candidate_id).raw_text == "Ada Example Python Flask"
    payload = client.get(f"/api/candidates/{candidate_id}/analysis").json
    assert payload["resume_text"] == "Ada Example Python Flask"
    assert payload["resume"]["status"] == "failed"
    # A generic failure must not leak provider internals.
    assert "provider down" not in payload["resume"]["error_message"]

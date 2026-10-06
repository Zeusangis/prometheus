from pathlib import Path

import pytest
from flask_migrate import check, downgrade, upgrade
from sqlalchemy import text

from app import create_app
from models import Candidate, ResumeAnalysis, GitHubAnalysis, RepositoryAnalysis, db

MIGRATIONS = str(Path(__file__).resolve().parents[1] / "migrations")


def test_fresh_schema_has_no_drift(app):
    with app.app_context():
        check(directory=MIGRATIONS)


def test_legacy_state_backfill_and_roundtrip(tmp_path):
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(tmp_path / "legacy.sqlite"),
        "UPLOAD_FOLDER": str(tmp_path / "uploads"),
    })
    old_states = ["queued", "uploaded", "processed", "failed", "ats_scored", "interview_scheduled", "hired", "rejected", None]
    with app.app_context():
        upgrade(directory=MIGRATIONS, revision="f87109fe65cc")
        for index, state in enumerate(old_states, 1):
            db.session.execute(text("INSERT INTO candidates (id, original_filename, file_path, status) VALUES (:id, 'test.pdf', :path, :status)"), {"id": index, "path": f"/test/{index}.pdf", "status": state})
        db.session.commit()
        upgrade(directory=MIGRATIONS)
        candidates = Candidate.query.order_by(Candidate.id).all()
        assert [c.status for c in candidates] == ["screening"] * 5 + ["interview_scheduled", "hired", "rejected", "screening"]
        assert [c.analysis_status for c in candidates[:5]] == ["queued", "queued", "partial", "failed", "partial"]
        assert len(candidates) == 9
        assert ResumeAnalysis.query.count() == 9
        assert all(c.resume_analysis.status == "pending" and c.resume_analysis.ats_score is None for c in candidates)
        db.session.remove()
        downgrade(directory=MIGRATIONS, revision="f87109fe65cc")
        upgrade(directory=MIGRATIONS)
        assert Candidate.query.count() == ResumeAnalysis.query.count() == 9
        check(directory=MIGRATIONS)
        db.session.remove()
        db.engine.dispose()


def test_analysis_migration_preserves_legacy_data_and_roundtrip(tmp_path):
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(tmp_path / "analysis-legacy.sqlite"),
        "UPLOAD_FOLDER": str(tmp_path / "uploads"),
    })
    with app.app_context():
        upgrade(directory=MIGRATIONS, revision="b730cce208a1")
        db.session.execute(text("""
            INSERT INTO candidates (id, original_filename, file_path, status, analysis_status,
                                    github_username, raw_text, ats_score)
            VALUES (1, 'legacy.pdf', '/legacy/resume.pdf', 'interview_scheduled', 'partial',
                    'legacy-user', 'Preserved original evidence', 42)
        """))
        db.session.commit()
        upgrade(directory=MIGRATIONS)
        candidate = db.session.get(Candidate, 1)
        assert candidate.raw_text == "Preserved original evidence"
        assert candidate.ats_score == 42
        assert candidate.status == "interview_scheduled"
        assert candidate.resume_analysis.status == "pending"
        assert candidate.resume_analysis.ats_score is None
        assert candidate.github_analysis.username == "legacy-user"
        assert candidate.github_analysis.total_stars is None
        # Measured repository output can be persisted and serialized independently.
        candidate.github_analysis.repositories.append(RepositoryAnalysis(
            repo_name="legacy-user/project", repo_url="https://github.com/legacy-user/project",
            evidence_metadata={"source": "test-fixture"},
        ))
        db.session.commit()
        assert candidate.github_analysis.to_dict()["repositories"][0]["repo_name"] == "legacy-user/project"
        db.session.remove()
        downgrade(directory=MIGRATIONS, revision="b730cce208a1")
        assert db.session.get(Candidate, 1).raw_text == "Preserved original evidence"
        db.session.remove()
        upgrade(directory=MIGRATIONS)
        assert Candidate.query.count() == ResumeAnalysis.query.count() == GitHubAnalysis.query.count() == 1
        assert RepositoryAnalysis.query.count() == 0
        check(directory=MIGRATIONS)
        db.session.remove()
        db.engine.dispose()


def test_production_requires_secret(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "dev-secret-key")
    with pytest.raises(ValueError, match="SECRET_KEY"):
        create_app()


def test_health_and_cors(client):
    assert client.get("/api/health").json["service"] == "TrueHire"
    response = client.get("/api/health", headers={"Origin": "https://untrusted.example.invalid"})
    assert "Access-Control-Allow-Origin" not in response.headers
    response = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"


def test_internal_errors_are_safe(app, client, monkeypatch):
    def explode():
        raise RuntimeError("provider-secret /private/database/path traceback")
    # Replace an existing view; authenticated fixtures already made requests.
    monkeypatch.setitem(app.view_functions, "jobs.list_jobs", explode)
    response = client.get("/api/jobs")
    assert response.status_code == 500
    assert response.json["error"]["code"] == "internal_error"
    assert "request_id" in response.json["error"]
    assert "provider-secret" not in str(response.json)
    assert "traceback" not in str(response.json)

from pathlib import Path

import pytest
from flask_migrate import check, downgrade, upgrade
from sqlalchemy import text

from app import create_app
from models import Candidate, db

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
        db.session.remove()
        downgrade(directory=MIGRATIONS, revision="f87109fe65cc")
        upgrade(directory=MIGRATIONS)
        assert Candidate.query.count() == 9
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


def test_internal_errors_are_safe(app, client):
    @app.get("/api/test-error")
    def explode():
        raise RuntimeError("provider-secret /private/database/path traceback")
    response = client.get("/api/test-error")
    assert response.status_code == 500
    assert response.json["error"]["code"] == "internal_error"
    assert "request_id" in response.json["error"]
    assert "provider-secret" not in str(response.json)
    assert "traceback" not in str(response.json)

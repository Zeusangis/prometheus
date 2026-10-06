import io
import os
from pathlib import Path
from types import SimpleNamespace

os.environ["FLASK_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-only-not-production"
os.environ["CELERY_BROKER_URL"] = "memory://"
os.environ["CELERY_RESULT_BACKEND"] = "cache+memory://"

import pytest
from flask_migrate import upgrade
from flask.testing import FlaskClient
from PyPDF2 import PdfWriter

from app import create_app
from models import Organization, OrganizationMembership, User, db
from services.analysis_queue import process_resume_task

MIGRATIONS = str(Path(__file__).resolve().parents[1] / "migrations")


@pytest.fixture
def app(tmp_path, monkeypatch):
    # A developer's local provider key must never make tests call a live service.
    monkeypatch.setenv("GEMINI_API_KEY", "")
    application = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + str(tmp_path / "test.sqlite"),
        "UPLOAD_FOLDER": str(tmp_path / "uploads"),
        "CELERY": {"broker_url": "memory://", "result_backend": "cache+memory://"},
    })
    monkeypatch.setattr(process_resume_task, "delay", lambda *_: SimpleNamespace(id="test-task"))
    with application.app_context():
        upgrade(directory=MIGRATIONS)
        user = User(email="recruiter@example.invalid", name="Test Recruiter")
        user.set_password("test-password-long-enough")
        org = Organization(name="Example Test Organization")
        db.session.add_all([user, org])
        db.session.flush()
        db.session.add(OrganizationMembership(user_id=user.id, organization_id=org.id, role="owner"))
        db.session.commit()
    yield application
    with application.app_context():
        db.session.remove()
        db.engine.dispose()


class RecruiterClient(FlaskClient):
    def open(self, *args, **kwargs):
        # Test browser-like header injection; auth/CSRF guard remains enabled.
        if kwargs.get("method", "GET") not in {"GET", "HEAD", "OPTIONS"}:
            with self.session_transaction() as stored:
                token = stored.get("csrf_token")
            if token:
                kwargs.setdefault("headers", {}).setdefault("X-CSRF-Token", token)
        return super().open(*args, **kwargs)


@pytest.fixture
def client(app):
    client = RecruiterClient(app, app.response_class)
    client.get("/api/auth/csrf")
    response = client.post("/api/auth/login", json={
        "email": "recruiter@example.invalid", "password": "test-password-long-enough",
    })
    assert response.status_code == 200, response.json
    return client


@pytest.fixture
def job_payload():
    return {
        "job": {
            "title": "Test Engineering Role", "company": "Example Test Organization",
            "jobType": "Full-time", "location": "Remote", "description": "Build tested Python systems.",
            "languages": ["Python"], "frameworks": ["Flask"],
        },
        "scraper": {"scraperMetrics": {"languageMatch": {"enabled": True, "weight": 80}}},
        "interview": {"interviewTone": "conversational", "interviewLength": 20},
    }


@pytest.fixture
def job_id(client, job_payload):
    response = client.post("/api/jobs", json=job_payload)
    assert response.status_code == 201, response.json
    return int(response.json["id"].removeprefix("job_"))


@pytest.fixture
def pdf_bytes():
    buffer = io.BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    writer.write(buffer)
    return buffer.getvalue()


@pytest.fixture
def apply(client, job_id, pdf_bytes):
    def submit(content=None, filename="resume.pdf", mimetype="application/pdf", endpoint=None, github_username="test-user"):
        data = {"full_name": "Test Applicant", "email": "applicant@example.invalid", "github_username": github_username}
        if filename is not None:
            data["resume"] = (io.BytesIO(content if content is not None else pdf_bytes), filename, mimetype)
        return client.post(endpoint or f"/api/public/jobs/{job_id}/apply", data=data)
    return submit

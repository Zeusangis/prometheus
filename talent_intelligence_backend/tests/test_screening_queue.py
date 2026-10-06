import io

import pytest

from models import Candidate, Job, Organization, OrganizationMembership, User, db


def submit(client, job_id, pdf_bytes, full_name, email, github_username=None):
    data = {"full_name": full_name, "email": email}
    if github_username:
        data["github_username"] = github_username
    data["resume"] = (io.BytesIO(pdf_bytes), "resume.pdf", "application/pdf")
    return client.post(f"/api/public/jobs/{job_id}/apply", data=data)


def names(rows):
    return [row["full_name"] for row in rows]


def seed_second_organization(app):
    """Create a rival organization whose applicants must never appear in the queue."""
    with app.app_context():
        user = User(email="rival@example.invalid", name="Rival Recruiter")
        user.set_password("rival-password-long-enough")
        org = Organization(name="Rival Organization")
        db.session.add_all([user, org])
        db.session.flush()
        db.session.add(OrganizationMembership(user_id=user.id, organization_id=org.id, role="owner"))
        job = Job(organization_id=org.id, title="Rival Role", company=org.name, status="open")
        db.session.add(job)
        db.session.flush()
        db.session.add(Candidate(
            full_name="Rival Applicant", email="rival.applicant@example.invalid",
            original_filename="rival.pdf", file_path="/tmp/rival.pdf",
            status="screening", analysis_status="queued", job_id=job.id,
        ))
        db.session.commit()


@pytest.fixture
def queue(client, pdf_bytes, job_id):
    """Three applicants: one still screening, one moved forward, one rejected."""
    screening = submit(client, job_id, pdf_bytes, "Ada Queue", "ada.queue@example.invalid").json["candidateId"]
    interview = submit(client, job_id, pdf_bytes, "Grace Queue", "grace.queue@example.invalid").json["candidateId"]
    rejected = submit(client, job_id, pdf_bytes, "Linus Queue", "linus.queue@example.invalid").json["candidateId"]
    assert client.post(f"/api/candidates/{interview}/stage", json={"stage": "interview_scheduled"}).status_code == 200
    assert client.post(f"/api/candidates/{rejected}/stage", json={"stage": "rejected"}).status_code == 200
    return {"screening": screening, "interview": interview, "rejected": rejected}


def test_queue_requires_authentication(app):
    assert app.test_client().get("/api/candidates").status_code == 401


def test_queue_lists_own_applicants_with_job_title(client, queue, job_id):
    response = client.get("/api/candidates")
    assert response.status_code == 200
    rows = response.json["candidates"]
    assert sorted(names(rows)) == ["Ada Queue", "Grace Queue", "Linus Queue"]
    assert {row["job_title"] for row in rows} == {"Test Engineering Role"}
    assert [row["id"] for row in rows] == sorted((row["id"] for row in rows), reverse=True)
    for row in rows:
        assert row["job_id"] == job_id
        assert row["uploaded_at"]
        assert isinstance(row["allowed_actions"], list)
    screening = next(row for row in rows if row["id"] == queue["screening"])
    assert screening["allowed_actions"] == ["interview_scheduled", "rejected"]
    # Terminal stages offer no further action, and the queue never invents one.
    assert next(row for row in rows if row["id"] == queue["rejected"])["allowed_actions"] == []


def test_queue_excludes_other_organizations(client, queue, app):
    seed_second_organization(app)
    rows = client.get("/api/candidates").json["candidates"]
    assert len(rows) == 3
    assert "Rival Applicant" not in names(rows)


def test_queue_stage_filter(client, queue):
    rows = client.get("/api/candidates?stage=interview_scheduled").json["candidates"]
    assert names(rows) == ["Grace Queue"]
    assert rows[0]["status"] == "interview_scheduled"


def test_queue_rejects_unknown_stage(client, queue):
    response = client.get("/api/candidates?stage=ghosted")
    assert response.status_code == 400
    assert response.json["error"]["code"] == "stage_invalid"


def test_queue_rejects_unknown_analysis_status(client, queue):
    response = client.get("/api/candidates?analysis_status=enqueued")
    assert response.status_code == 400
    assert response.json["error"]["code"] == "analysis_status_invalid"


def test_queue_attention_filter_uses_retryable_states(client, queue, app):
    with app.app_context():
        db.session.get(Candidate, queue["screening"]).analysis_status = "failed"
        db.session.get(Candidate, queue["interview"]).analysis_status = "complete"
        db.session.commit()
    rows = client.get("/api/candidates?attention=1").json["candidates"]
    assert names(rows) == ["Ada Queue"]
    assert rows[0]["analysis_status"] == "failed"


def test_queue_running_filter(client, queue, app):
    with app.app_context():
        db.session.get(Candidate, queue["screening"]).analysis_status = "partial"
        db.session.get(Candidate, queue["rejected"]).analysis_status = "running"
        db.session.commit()
    rows = client.get("/api/candidates?running=1").json["candidates"]
    # Grace is still queued, Linus is running, Ada is partial (not in flight).
    assert sorted(names(rows)) == ["Grace Queue", "Linus Queue"]


def test_queue_search_matches_name_and_email(client, queue):
    assert names(client.get("/api/candidates?q=grace").json["candidates"]) == ["Grace Queue"]
    assert names(client.get("/api/candidates?q=linus.queue@").json["candidates"]) == ["Linus Queue"]
    assert client.get("/api/candidates?q=nobody").json["candidates"] == []


def test_queue_job_filter_requires_owned_job(client, queue, job_id):
    assert len(client.get(f"/api/candidates?job_id=job_{job_id}").json["candidates"]) == 3
    assert client.get(f"/api/candidates?job_id={job_id + 99}").status_code == 404
    assert client.get("/api/candidates?job_id=not-a-job").status_code == 400


def test_job_list_reports_real_stage_counts(client, queue):
    jobs = client.get("/api/jobs").json["jobs"]
    assert len(jobs) == 1
    assert jobs[0]["total_applicants"] == 3
    assert jobs[0]["stage_counts"] == {"screening": 1, "interview_scheduled": 1, "rejected": 1}
    assert jobs[0]["interviewing_count"] == 1


def test_job_list_counts_ignore_other_organizations(client, queue, app):
    seed_second_organization(app)
    job = client.get("/api/jobs").json["jobs"][0]
    assert job["total_applicants"] == 3
    assert job["stage_counts"] == {"screening": 1, "interview_scheduled": 1, "rejected": 1}
    assert job["interviewing_count"] == 1

import io

import pytest

from models import Candidate, Job, Organization, OrganizationMembership, User, db
from models.stage_event import ImmutableAuditRecord, StageEvent


def submit(client, job_id, pdf_bytes, full_name, email):
    data = {
        "full_name": full_name,
        "email": email,
        "resume": (io.BytesIO(pdf_bytes), "resume.pdf", "application/pdf"),
    }
    return client.post(f"/api/public/jobs/{job_id}/apply", data=data)


def events(client, candidate_id):
    response = client.get(f"/api/candidates/{candidate_id}/stage-events")
    assert response.status_code == 200, response.json
    return response.json["events"]


def seed_rival_candidate(app):
    """A candidate owned by a different organization, to prove the trail is scoped."""
    with app.app_context():
        user = User(email="rival.audit@example.invalid", name="Rival Audit Recruiter")
        user.set_password("rival-password-long-enough")
        org = Organization(name="Rival Audit Organization")
        db.session.add_all([user, org])
        db.session.flush()
        db.session.add(OrganizationMembership(user_id=user.id, organization_id=org.id, role="owner"))
        job = Job(organization_id=org.id, title="Rival Audit Role", company=org.name, status="open")
        db.session.add(job)
        db.session.flush()
        candidate = Candidate(
            full_name="Rival Audit Applicant",
            email="rival.audit.applicant@example.invalid",
            original_filename="rival.pdf",
            file_path="/tmp/rival-audit.pdf",
            status="interview_scheduled",
            analysis_status="queued",
            job_id=job.id,
        )
        db.session.add(candidate)
        db.session.commit()
        return candidate.id


def test_stage_change_is_recorded_with_actor_and_stages(client, pdf_bytes, job_id):
    candidate_id = submit(client, job_id, pdf_bytes, "Ada Audit", "ada.audit@example.invalid").json["candidateId"]
    assert client.post(f"/api/candidates/{candidate_id}/stage", json={"stage": "interview_scheduled"}).status_code == 200

    recorded = events(client, candidate_id)
    assert len(recorded) == 1
    event = recorded[0]
    assert event["event_type"] == "stage_changed"
    assert event["from_stage"] == "screening"
    assert event["to_stage"] == "interview_scheduled"
    assert event["actor_email"] == "recruiter@example.invalid"
    assert event["created_at"]


def test_refused_transition_records_nothing(client, pdf_bytes, job_id):
    candidate_id = submit(client, job_id, pdf_bytes, "Grace Audit", "grace.audit@example.invalid").json["candidateId"]
    # screening -> hired is not a legal transition, so the trail must gain nothing.
    assert client.post(f"/api/candidates/{candidate_id}/stage", json={"stage": "hired"}).status_code == 409
    assert events(client, candidate_id) == []


def test_events_are_newest_first(client, pdf_bytes, job_id):
    candidate_id = submit(client, job_id, pdf_bytes, "Linus Audit", "linus.audit@example.invalid").json["candidateId"]
    client.post(f"/api/candidates/{candidate_id}/stage", json={"stage": "interview_scheduled"})
    client.post(f"/api/candidates/{candidate_id}/stage", json={"stage": "interview_completed"})

    recorded = events(client, candidate_id)
    assert [event["to_stage"] for event in recorded] == ["interview_completed", "interview_scheduled"]
    assert [event["from_stage"] for event in recorded] == ["interview_scheduled", "screening"]
    assert recorded[0]["id"] > recorded[1]["id"]


def test_rejection_is_recorded_like_any_other_change(client, pdf_bytes, job_id):
    candidate_id = submit(client, job_id, pdf_bytes, "Karen Audit", "karen.audit@example.invalid").json["candidateId"]
    assert client.post(f"/api/candidates/{candidate_id}/stage", json={"stage": "rejected"}).status_code == 200
    recorded = events(client, candidate_id)
    assert recorded[0]["from_stage"] == "screening"
    assert recorded[0]["to_stage"] == "rejected"


def test_analysis_retry_records_the_status_it_replaced(client, app, pdf_bytes, job_id):
    candidate_id = submit(client, job_id, pdf_bytes, "Margaret Audit", "margaret.audit@example.invalid").json["candidateId"]
    with app.app_context():
        candidate = db.session.get(Candidate, candidate_id)
        candidate.analysis_status = "failed"
        db.session.commit()

    assert client.post(f"/api/candidates/{candidate_id}/analysis/retry").status_code == 202
    recorded = events(client, candidate_id)
    assert len(recorded) == 1
    assert recorded[0]["event_type"] == "analysis_retried"
    assert recorded[0]["previous_analysis_status"] == "failed"
    assert recorded[0]["actor_email"] == "recruiter@example.invalid"
    assert recorded[0]["from_stage"] is None and recorded[0]["to_stage"] is None


def test_refused_retry_records_nothing(client, pdf_bytes, job_id):
    candidate_id = submit(client, job_id, pdf_bytes, "Barbara Audit", "barbara.audit@example.invalid").json["candidateId"]
    # A freshly applied candidate is `queued`, so retry is refused and nothing is recorded.
    assert client.post(f"/api/candidates/{candidate_id}/analysis/retry").status_code == 409
    assert events(client, candidate_id) == []


def test_trail_mixes_stage_changes_and_retries_without_losing_either(client, app, pdf_bytes, job_id):
    candidate_id = submit(client, job_id, pdf_bytes, "Alan Audit", "alan.audit@example.invalid").json["candidateId"]
    client.post(f"/api/candidates/{candidate_id}/stage", json={"stage": "interview_scheduled"})
    with app.app_context():
        candidate = db.session.get(Candidate, candidate_id)
        candidate.analysis_status = "partial"
        db.session.commit()
    client.post(f"/api/candidates/{candidate_id}/analysis/retry")

    kinds = [event["event_type"] for event in events(client, candidate_id)]
    assert sorted(kinds) == ["analysis_retried", "stage_changed"]


def test_events_are_organization_scoped(client, app):
    rival_id = seed_rival_candidate(app)
    assert client.get(f"/api/candidates/{rival_id}/stage-events").status_code == 404


def test_another_organizations_events_never_appear(client, app, pdf_bytes, job_id):
    rival_id = seed_rival_candidate(app)
    own_id = submit(client, job_id, pdf_bytes, "Edsger Audit", "edsger.audit@example.invalid").json["candidateId"]
    client.post(f"/api/candidates/{own_id}/stage", json={"stage": "interview_scheduled"})

    assert [event["to_stage"] for event in events(client, own_id)] == ["interview_scheduled"]
    with app.app_context():
        assert db.session.scalars(
            db.select(StageEvent).where(StageEvent.candidate_id == rival_id)
        ).all() == []


def test_audit_endpoint_requires_authentication(app, pdf_bytes, job_id):
    assert app.test_client().get("/api/candidates/1/stage-events").status_code == 401


def test_recorded_events_cannot_be_updated(app, client, pdf_bytes, job_id):
    candidate_id = submit(client, job_id, pdf_bytes, "Donald Audit", "donald.audit@example.invalid").json["candidateId"]
    client.post(f"/api/candidates/{candidate_id}/stage", json={"stage": "interview_scheduled"})

    with app.app_context():
        event = db.session.scalars(db.select(StageEvent)).one()
        event.to_stage = "hired"
        with pytest.raises(ImmutableAuditRecord):
            db.session.commit()
        db.session.rollback()
        assert db.session.get(StageEvent, event.id).to_stage == "interview_scheduled"


def test_recorded_events_cannot_be_deleted(app, client, pdf_bytes, job_id):
    candidate_id = submit(client, job_id, pdf_bytes, "Frances Audit", "frances.audit@example.invalid").json["candidateId"]
    client.post(f"/api/candidates/{candidate_id}/stage", json={"stage": "rejected"})

    with app.app_context():
        event = db.session.scalars(db.select(StageEvent)).one()
        event_id = event.id
        db.session.delete(event)
        with pytest.raises(ImmutableAuditRecord):
            db.session.commit()
        db.session.rollback()
        assert db.session.get(StageEvent, event_id) is not None


def test_an_audit_failure_never_blocks_the_stage_change(client, monkeypatch, pdf_bytes, job_id):
    candidate_id = submit(client, job_id, pdf_bytes, "Tim Audit", "tim.audit@example.invalid").json["candidateId"]

    def unavailable(**kwargs):
        raise RuntimeError("audit store unavailable")

    monkeypatch.setattr("services.audit.StageEvent", unavailable)
    response = client.post(f"/api/candidates/{candidate_id}/stage", json={"stage": "interview_scheduled"})
    assert response.status_code == 200
    assert response.json["status"] == "interview_scheduled"


def test_an_audit_failure_never_blocks_an_analysis_retry(client, app, monkeypatch, pdf_bytes, job_id):
    candidate_id = submit(client, job_id, pdf_bytes, "John Audit", "john.audit@example.invalid").json["candidateId"]
    with app.app_context():
        candidate = db.session.get(Candidate, candidate_id)
        candidate.analysis_status = "failed"
        db.session.commit()

    def unavailable(**kwargs):
        raise RuntimeError("audit store unavailable")

    monkeypatch.setattr("services.audit.StageEvent", unavailable)
    response = client.post(f"/api/candidates/{candidate_id}/analysis/retry")
    assert response.status_code == 202
    assert response.json["analysis_status"] == "queued"

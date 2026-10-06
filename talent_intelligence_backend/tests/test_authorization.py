import io

import pytest

from models import Organization, OrganizationMembership, User, db


@pytest.fixture
def outsider(app):
    with app.app_context():
        user = User(email="outsider@example.invalid", name="Outside Recruiter")
        user.set_password("outside-test-password")
        org = Organization(name="Outside Test Organization")
        db.session.add_all([user, org])
        db.session.flush()
        db.session.add(OrganizationMembership(user_id=user.id, organization_id=org.id))
        db.session.commit()
    browser = app.test_client()
    token = browser.get("/api/auth/csrf").json["csrf_token"]
    response = browser.post("/api/auth/login", headers={"X-CSRF-Token": token}, json={
        "email": "outsider@example.invalid", "password": "outside-test-password",
    })
    assert response.status_code == 200
    return browser, {"X-CSRF-Token": response.json["csrf_token"]}


def test_cross_org_reads_and_writes(outsider, apply, job_id):
    candidate_id = apply().json["candidateId"]
    browser, headers = outsider
    for path in [f"/api/jobs/{job_id}", f"/api/jobs/{job_id}/info", f"/api/jobs/{job_id}/applicants", f"/api/candidates/{candidate_id}", f"/api/candidates/{candidate_id}/analysis"]:
        assert browser.get(path).status_code == 404, path
    for method, path, payload in [
        ("PATCH", f"/api/jobs/{job_id}", {"title": "Stolen"}),
        ("POST", f"/api/jobs/{job_id}/status", {"status": "closed"}),
        ("POST", f"/api/jobs/{job_id}/scraper", {}),
        ("POST", f"/api/jobs/{job_id}/interview", {}),
        ("POST", f"/api/candidates/{candidate_id}/stage", {"stage": "rejected"}),
        ("POST", f"/api/candidates/{candidate_id}/analysis/retry", {}),
        ("POST", f"/api/jobs/{job_id}/candidates/{candidate_id}/next-step", {"status": "rejected"}),
    ]:
        assert browser.open(path, method=method, json=payload, headers=headers).status_code == 404, path
    assert browser.get("/api/jobs").json["jobs"] == []
    assert browser.get("/api/jobs/my-company").json["jobs"] == []


def test_cannot_inject_ownership(client, job_payload, outsider):
    job_payload["organization_id"] = 999
    job_payload["job"]["company"] = "Spoofed Company"
    job_id = client.post("/api/jobs", json=job_payload).json["id"]
    detail = client.get(f"/api/jobs/{job_id}").json["job"]
    assert detail["company"] == "Example Test Organization"
    assert detail["organization_id"] != 999
    changed = client.patch(f"/api/jobs/{job_id}", json={"organization_id": 999, "company": "Spoofed", "recruiter_data": {"email": "fake"}}).json["job"]
    assert changed["organization_id"] == detail["organization_id"]
    assert changed["company"] == detail["company"]
    assert changed["recruiter_data"] is None


def test_public_application_remains_unauthenticated(app, job_id, pdf_bytes):
    public = app.test_client()
    assert public.get(f"/api/public/jobs/{job_id}").status_code == 200
    response = public.post(f"/api/public/jobs/{job_id}/apply", data={
        "full_name": "Public Test Applicant", "email": "public@example.invalid",
        "resume": (io.BytesIO(pdf_bytes), "public.pdf"),
    })
    assert response.status_code == 200
    assert public.get(f"/api/candidates/{response.json['candidateId']}").status_code == 401
    assert public.get(f"/api/candidates/{response.json['candidateId']}/analysis").status_code == 401
